"""Persistent virtual devices and serialized MQTT transmission."""
import asyncio
from uuid import uuid4
from homeassistant.components import mqtt
from homeassistant.helpers.storage import Store
from .const import DOMAIN, PLATFORMS
from .codec import raw_to_tuya
from .protocols import encode_command


def validate_device(data):
    if not isinstance(data, dict):
        raise ValueError("Device must be an object")
    allowed = {"name", "device_type", "topic", "protocol", "address", "commands"}
    if set(data) - allowed:
        raise ValueError("Unknown device fields")
    for key in ("name", "device_type", "topic", "protocol"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ValueError(f"Missing {key}")
    data = dict(data)
    data["name"] = data["name"].strip()
    if len(data["name"]) > 100 or data["device_type"] not in PLATFORMS:
        raise ValueError("Invalid name or device type")
    topic = data["topic"]
    if len(topic) > 512 or any(c in topic for c in ("+", "#", "\x00")) or not topic.endswith("/set/ir_code_to_send"):
        raise ValueError("Use a concrete MQTT topic ending /set/ir_code_to_send")
    if data["device_type"] == "climate":
        if data["protocol"] != "electra":
            raise ValueError("Only Electra AC is implemented in this preview")
    else:
        if data["protocol"] not in ("nec", "samsung"):
            raise ValueError("Select NEC or Samsung")
        commands = data.get("commands", {})
        if not isinstance(commands, dict) or not 1 <= len(commands) <= 100:
            raise ValueError("Provide 1..100 named numeric commands")
        for key, code in commands.items():
            if not isinstance(key, str) or not 1 <= len(key) <= 64:
                raise ValueError("Invalid command name")
            encode_command(data["protocol"], data.get("address", 0), code)
        if data["device_type"] in ("light", "media_player") and not {"turn_on", "turn_off"} <= commands.keys():
            raise ValueError("Provide turn_on and turn_off commands")
    return data


class Hub:
    def __init__(self, hass, entry):
        self.hass, self.entry = hass, entry
        self.store = Store(hass, 1, f"{DOMAIN}.devices")
        self.devices = []
        self.adders = {}
        self.lock = asyncio.Lock()
        self.tx_locks = {}

    async def load(self):
        self.devices = await self.store.async_load() or []

    async def create(self, data):
        device = validate_device(data)
        async with self.lock:
            device["id"] = uuid4().hex
            updated = [*self.devices, device]
            await self.store.async_save(updated)
            self.devices = updated
            self.adders[device["device_type"]](device)
        return device

    async def send(self, device, raw):
        payload = raw_to_tuya(raw)
        topic = device["topic"]
        async with self.tx_locks.setdefault(topic, asyncio.Lock()):
            await mqtt.async_publish(self.hass, topic, payload, qos=0, retain=False)
            # Conservative pacing; this is not a hardware acknowledgement.
            await asyncio.sleep(max(0.5, sum(raw) / 1_000_000 + 0.1))
