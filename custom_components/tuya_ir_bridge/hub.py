"""Persistent virtual devices and local upstream protocol engine."""
import asyncio
import copy
from uuid import uuid4
from homeassistant.components import mqtt
from homeassistant.helpers.storage import Store
from homeassistant.helpers import device_registry as dr
from .const import DOMAIN, PLATFORMS
from .native import NativeEngine
from .protocols import encode_command
from .signal import prepare_signal
from .commands import normalize_hvac, normalize_keys


def validate_device(data, catalogue):
    if not isinstance(data, dict):
        raise ValueError("Device must be an object")
    allowed = {"name", "device_type", "topic", "protocol", "address", "commands", "model", "transport", "hvac_options", "min_temp", "max_temp", "temp_step"}
    if set(data) - allowed:
        raise ValueError("Unknown device fields")
    data = copy.deepcopy(data)
    for key in ("name", "device_type", "topic", "protocol"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ValueError(f"Missing {key}")
    data["name"] = data["name"].strip()
    if len(data["name"]) > 100 or data["device_type"] not in PLATFORMS:
        raise ValueError("Invalid name or device type")
    topic = data["topic"]
    if len(topic) > 512 or any(c in topic for c in ("+", "#", "\x00")) or not topic.endswith("/set/ir_code_to_send"):
        raise ValueError("Use a concrete MQTT topic ending /set/ir_code_to_send")
    if data.get("transport", "zosung") not in ("zosung", "base64"):
        raise ValueError("Invalid transport")
    data.setdefault("transport", "zosung")
    protocol = data["protocol"].upper()
    if protocol == "ELECTRA":
        protocol = "ELECTRA_AC"
    data["protocol"] = protocol
    if data["device_type"] == "climate":
        if protocol not in catalogue["climate"]:
            raise ValueError("Protocol is not supported by the bundled HVAC engine")
        model = data.get("model", -1)
        if type(model) is not int or not -1 <= model <= 32767:
            raise ValueError("Model must be an integer from -1 to 32767")
        options = normalize_hvac(data.get("hvac_options", {}))
        data["hvac_options"] = options
        allowed_options = {"SwingV", "SwingH", "Quiet", "Turbo", "Econo", "Light", "Filter", "Clean", "Beep", "iFeel", "Sleep", "Clock", "SensorTemp"}
        if not isinstance(options, dict) or set(options) - allowed_options:
            raise ValueError("Invalid HVAC options")
        for key in ("min_temp", "max_temp", "temp_step"):
            value = data.get(key, {"min_temp":16,"max_temp":30,"temp_step":1}[key])
            if type(value) not in (int, float) or not 0 < value <= 50:
                raise ValueError(f"Invalid {key}")
        if data.get("min_temp",16) >= data.get("max_temp",30):
            raise ValueError("Minimum temperature must be below maximum")
    else:
        if protocol not in {p["name"] for p in catalogue["send"]}:
            raise ValueError("Protocol is not supported by the bundled IRsend engine")
        commands = data.get("commands", {})
        if not isinstance(commands, dict) or not 1 <= len(commands) <= 100:
            raise ValueError("Provide 1..100 named IRsend commands")
        for key, command in commands.items():
            if not isinstance(key, str) or not 1 <= len(key) <= 64 or not isinstance(command, (dict, int)) or isinstance(command, bool):
                raise ValueError("Each command must be a named IRsend object")
        if data["device_type"] in ("light", "media_player") and not {"turn_on", "turn_off"} <= commands.keys():
            raise ValueError("Provide turn_on and turn_off commands")
    return data


class Hub:
    def __init__(self, hass, entry):
        self.hass, self.entry = hass, entry
        self.store = Store(hass, 1, f"{DOMAIN}.devices")
        self.devices, self.adders, self.entities = [], {}, {}
        self.lock, self.tx_locks = asyncio.Lock(), {}
        self.engine = NativeEngine()

    async def load(self):
        await self.hass.async_add_executor_job(self.engine.prepare)
        self.catalogue = await self.engine.request({"op": "catalogue"})
        self.catalogue["send"].append({"name": "RAW", "bits": 0, "state": False})
        self.catalogue["notes"] = {
            "YORK": "Upstream advertises HVAC support but its common-state dispatch fails; use a documented IRsend state instead.",
            "MIDEA": "Some feature combinations produce internal gaps beyond the Tuya limit and will be rejected.",
            "CARRIER_AC40": "The default signal contains a gap beyond the Tuya limit.",
            "MULTIBRACKETS": "The default signal contains a gap beyond the Tuya limit.",
            "FUJITSU_AC": "IRsend requires an explicit Bits value appropriate to the state length.",
            "MWM": "IRsend requires an explicit Bits value appropriate to the state length.",
        }
        self.devices = await self.store.async_load() or []

    async def create(self, data):
        device = validate_device(data, self.catalogue)
        await self.validate_encoding(device)
        async with self.lock:
            device["id"] = uuid4().hex
            updated = [*self.devices, device]
            await self.store.async_save(updated)
            self.devices = updated
            self.adders[device["device_type"]](device)
        return device

    async def validate_encoding(self, device):
        # Encode before saving; never transmit during creation.
        if device["device_type"] == "climate":
            await self.hvac(device, {"Power": False, "Mode": "Auto", "Temp": max(device.get("min_temp",16), min(24,device.get("max_temp",30))), "FanSpeed": "Auto"})
        else:
            for name in device["commands"]:
                await self.command(device, name)

    async def update(self, device_id, data):
        device = validate_device(data, self.catalogue)
        async with self.lock:
            old = next((d for d in self.devices if d["id"] == device_id), None)
            if old is None:
                raise ValueError("Device no longer exists. Refresh the device list")
            if device["device_type"] != old["device_type"]:
                raise ValueError("Device type cannot be changed; create a separate device for a different type")
            await self.validate_encoding(device)
            device["id"] = device_id
            entity = next((e for e in self.entities.values() if e.device["id"] == device_id), None)
            # Wait for an in-flight command before replacing its parameters.
            async with entity._command_lock if entity else asyncio.Lock():
                updated = [device if d["id"] == device_id else d for d in self.devices]
                await self.store.async_save(updated)
                self.devices = updated
                registry = dr.async_get(self.hass)
                registered = registry.async_get_device(identifiers={(DOMAIN, device_id)})
                if registered:
                    registry.async_update_device(registered.id, name=device["name"], model=device["protocol"])
                if entity:
                    entity.apply_device(device)
        return device

    async def hvac(self, device, state, previous=None):
        protocol = device["protocol"].upper()
        state = {**device.get("hvac_options", {}), **state,
                 "Protocol": "ELECTRA_AC" if protocol == "ELECTRA" else protocol,
                 "Model": device.get("model", -1)}
        result = await self.engine.request({"op": "hvac", "state": state, "previous": previous})
        prepare_signal(result, device.get("transport", "base64"))
        return result, state

    async def command(self, device, name):
        command = device["commands"][name]
        if type(command) is int:
            # Preserve 0.1.x address/command-ID configurations exactly.
            raw = encode_command(device["protocol"].lower(), device.get("address", 0), command)
            return {"pulses": [[value if i%2==0 else -value,38000,50] for i,value in enumerate(raw)]}
        return await self.irsend(device, command)

    async def irsend(self, device, command):
        if isinstance(command, str):
            values = command.strip().split(",")
            if values[0].lower() == "raw":
                values = values[1:]
            values = [int(value.strip()) for value in values]
            if len(values) < 2:
                raise ValueError("Raw IRsend requires frequency followed by timings")
            command = {"Protocol": "RAW", "Frequency": values[0], "Data": values[1:]}
        command = normalize_keys(command, ("Protocol", "Bits", "Data", "Repeat", "Frequency"))
        command = {"Protocol": device["protocol"], **command}
        if str(command["Protocol"]).upper() == "RAW":
            if set(command) - {"Protocol", "Frequency", "Data"}:
                raise ValueError("RAW accepts Protocol, Frequency and Data")
            frequency = command.get("Frequency", 38000)
            if type(frequency) is not int:
                raise ValueError("Frequency must be an integer")
            frequency = frequency * 1000 if frequency < 1000 else frequency
            raw = command.get("Data")
            if not isinstance(raw, list) or not 1 <= len(raw) <= 4096 or any(type(v) is not int or not 0 < v <= 65535 for v in raw):
                raise ValueError("Raw Data must contain 1..4096 positive uint16 timings")
            result = {"pulses": [[v if i%2==0 else -v,frequency,50] for i,v in enumerate(raw)]}
            prepare_signal(result, device.get("transport", "base64"))
            return result
        if set(command) - {"Protocol", "Bits", "Data", "Repeat"}:
            raise ValueError("IRsend accepts Protocol, Bits, Data and Repeat")
        for key, low, high in (("Bits",1,4096),("Repeat",0,10)):
            if key in command and (type(command[key]) is not int or not low <= command[key] <= high):
                raise ValueError(f"{key} must be an integer in {low}..{high}")
        if type(command.get("Data")) is int:
            command["Data"] = hex(command["Data"])
        result = await self.engine.request({"op": "send", "command": command})
        prepare_signal(result, device.get("transport", "base64"))
        return result

    async def send(self, device, signal):
        payload, duration = prepare_signal(signal, device.get("transport", "base64"))
        topic = device["topic"]
        async with self.tx_locks.setdefault(topic, asyncio.Lock()):
            await mqtt.async_publish(self.hass, topic, payload, qos=0, retain=False)
            await asyncio.sleep(max(0.5, duration + 0.1))
