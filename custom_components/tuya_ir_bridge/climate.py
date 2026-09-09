"""Climate using upstream IRac with per-device previous state."""
from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode
from homeassistant.const import UnitOfTemperature, ATTR_TEMPERATURE, ATTR_UNIT_OF_MEASUREMENT
from homeassistant.exceptions import HomeAssistantError
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util.unit_conversion import TemperatureConverter
from .entity import IREntity, setup_platform
from homeassistant.helpers.restore_state import RestoreEntity
from .commands import normalize_hvac
from .const import HVAC_MODES, FAN_MODES, SWING_MODES

SWING_VALUES = {"off": ("Off", "Off"), "vertical": ("Auto", "Off"), "horizontal": ("Off", "Auto"), "both": ("Auto", "Auto")}
SWING_VALUES.update({key: (key.title(), "Off") for key in ("highest", "high", "middle", "low", "lowest")})
SWING_VALUES.update({key: ("Off", "Middle" if key == "horizontal middle" else key.title()) for key in ("left max", "left", "horizontal middle", "right", "right max", "wide")})


async def async_setup_entry(hass, entry, async_add_entities):
    setup_platform(hass, entry, async_add_entities, "climate", IRClimate)


class IRClimate(IREntity, ClimateEntity, RestoreEntity):
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp, _attr_max_temp = 16, 32
    _attr_target_temperature_step = 1
    _attr_target_temperature = 24
    _attr_hvac_mode = HVACMode.OFF
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.AUTO, HVACMode.COOL, HVACMode.HEAT, HVACMode.DRY, HVACMode.FAN_ONLY]
    _attr_fan_mode = "auto"
    _attr_fan_modes = ["auto", "min", "low", "medium", "high", "max"]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE

    def __init__(self, hub, device):
        super().__init__(hub, device)
        self._previous = None
        self._remove_linked = None
        self._attr_current_temperature = None
        self._attr_current_humidity = None
        self._attr_preset_mode = None
        self._pre_away_temperature = None
        self._last_active_mode = next((mode for mode in device.get("hvac_modes", HVAC_MODES) if mode != "off"), "auto")
        self._attr_min_temp = device.get("min_temp", 16)
        self._attr_max_temp = device.get("max_temp", 32 if device["protocol"].lower() in ("electra", "electra_ac") else 30)
        self._attr_target_temperature_step = device.get("temp_step", 1)
        self._attr_target_temperature = device.get("initial_target_temp", max(self._attr_min_temp, min(24, self._attr_max_temp)))
        self._attr_hvac_mode = HVACMode(device.get("initial_hvac_mode", "off"))
        self.configure_capabilities(device)

    def configure_capabilities(self, device):
        self._attr_temperature_unit = UnitOfTemperature.FAHRENHEIT if device.get("temperature_unit") == "F" else UnitOfTemperature.CELSIUS
        self._attr_precision = device.get("precision", 0.1)
        self._attr_hvac_modes = [HVACMode(v) for v in device.get("hvac_modes", HVAC_MODES)]
        self._attr_fan_modes = device.get("fan_modes", FAN_MODES)
        self._attr_swing_modes = device.get("swing_modes", [])
        self._attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
        if self._attr_fan_modes:
            self._attr_supported_features |= ClimateEntityFeature.FAN_MODE
        if self._attr_swing_modes:
            self._attr_supported_features |= ClimateEntityFeature.SWING_MODE
        self._attr_supported_features |= ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF
        away = device.get("away_temp", 0)
        self._attr_preset_modes = ["none", "away"] if away else []
        if away:
            self._attr_supported_features |= ClimateEntityFeature.PRESET_MODE
        if self._attr_hvac_mode not in self._attr_hvac_modes:
            self._attr_hvac_mode = HVACMode.OFF
        if self._attr_fan_mode not in self._attr_fan_modes:
            self._attr_fan_mode = next(iter(self._attr_fan_modes), "auto")

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last:
            self._previous = last.attributes.get("ir_previous_state")
            if last.state in self._attr_hvac_modes:
                self._attr_hvac_mode = HVACMode(last.state)
            self._attr_target_temperature = last.attributes.get("temperature", 24)
            self._attr_fan_mode = last.attributes.get("fan_mode", "auto")
        self.configure_capabilities(self.device)
        self._attr_target_temperature = max(self.min_temp, min(self.target_temperature, self.max_temp))
        self._subscribe_linked_entities()
        self.async_on_remove(self._remove_linked_entities)
        self.hub.notify()

    @callback
    def _remove_linked_entities(self):
        if self._remove_linked:
            self._remove_linked()
            self._remove_linked = None

    def _subscribe_linked_entities(self):
        if self._remove_linked:
            self._remove_linked()
            self._remove_linked = None
        entity_ids = [self.device.get(key) for key in ("temperature_sensor", "humidity_sensor", "power_sensor", "availability_sensor")]
        entity_ids = [entity_id for entity_id in entity_ids if entity_id]
        if entity_ids:
            self._remove_linked = async_track_state_change_event(self.hass, entity_ids, self._linked_state_changed)
        self._refresh_linked_state()

    @callback
    def _linked_state_changed(self, event):
        self._refresh_linked_state()
        self.async_write_ha_state()

    @callback
    def _refresh_linked_state(self):
        temperature = self.hass.states.get(self.device.get("temperature_sensor", ""))
        self._attr_current_temperature = self._state_number(temperature, temperature=True)
        humidity = self.hass.states.get(self.device.get("humidity_sensor", ""))
        self._attr_current_humidity = self._state_number(humidity)
        power = self.hass.states.get(self.device.get("power_sensor", ""))
        if power and power.state not in ("unknown", "unavailable"):
            if power.state.lower() in ("off", "false", "0") and self._attr_hvac_mode != HVACMode.OFF:
                self._last_active_mode = self._attr_hvac_mode
                self._attr_hvac_mode = HVACMode.OFF
            elif power.state.lower() in ("on", "true", "1") and self._attr_hvac_mode == HVACMode.OFF:
                mode = self._last_active_mode if self.device.get("keep_mode_on_power_on") else HVACMode(self.device.get("initial_hvac_mode", "auto"))
                self._attr_hvac_mode = mode if mode != HVACMode.OFF else next(v for v in self.hvac_modes if v != HVACMode.OFF)

    def _state_number(self, state, temperature=False):
        if state is None or state.state in ("unknown", "unavailable"):
            return None
        try:
            value = float(state.state)
            if temperature:
                source = state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
                if source in (UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT) and source != self.temperature_unit:
                    value = TemperatureConverter.convert(value, source, self.temperature_unit)
            return round(value, 2)
        except (TypeError, ValueError):
            return None

    @property
    def available(self):
        entity_id = self.device.get("availability_sensor")
        if not entity_id:
            return True
        if self.hass is None:
            return False
        state = self.hass.states.get(entity_id)
        return state is not None and state.state.lower() not in ("off", "false", "0", "unknown", "unavailable")

    @property
    def assumed_state(self):
        return not bool(self.device.get("power_sensor"))

    @property
    def extra_state_attributes(self):
        return {"ir_previous_state": self._previous}

    def apply_device(self, device):
        # A changed encoder/blaster/options invalidates the previous IR estimate.
        if any(self.device.get(key) != device.get(key) for key in ("protocol", "model", "topic", "hvac_options")):
            self._previous = None
        self._attr_min_temp = device.get("min_temp", 16)
        self._attr_max_temp = device.get("max_temp", 32 if device["protocol"].lower() in ("electra", "electra_ac") else 30)
        self._attr_target_temperature_step = device.get("temp_step", 1)
        self._attr_target_temperature = max(self._attr_min_temp, min(self._attr_target_temperature, self._attr_max_temp))
        self.configure_capabilities(device)
        super().apply_device(device)
        if self.hass is not None:
            self._subscribe_linked_entities()

    @property
    def swing_mode(self):
        state = {**self.device.get("hvac_options", {}), **(self._previous or {})}
        pair = (str(state.get("SwingV", "Off")).lower(), str(state.get("SwingH", "Off")).lower())
        return next((key for key, values in SWING_VALUES.items() if key in self.swing_modes and tuple(v.lower() for v in values) == pair), None)

    async def async_set_swing_mode(self, swing_mode):
        if swing_mode not in self.swing_modes:
            raise HomeAssistantError("Swing mode is not enabled for this device")
        vertical, horizontal = SWING_VALUES[swing_mode]
        await self._set(extra={"SwingV": vertical, "SwingH": horizontal})

    async def async_set_feature(self, feature, enabled):
        if feature not in self.device.get("feature_switches", []):
            raise HomeAssistantError("Feature switch is not enabled")
        value = enabled
        if feature in ("SwingV", "SwingH"):
            value = "Auto" if enabled else "Off"
        elif feature == "Sleep":
            value = self.device.get("sleep_minutes", 0) if enabled else -1
        await self._set(extra={feature: value})

    async def _set(self, mode=None, temperature=None, fan=None, extra=None):
        async with self._command_lock:
            mode = self._attr_hvac_mode if mode is None else mode
            temperature = self._attr_target_temperature if temperature is None else temperature
            fan = self._attr_fan_mode if fan is None else fan
            try:
                if isinstance(temperature, bool) or not self.min_temp <= temperature <= self.max_temp:
                    raise ValueError("Temperature outside configured device range")
                if mode not in self.hvac_modes or (self.fan_modes and fan not in self.fan_modes):
                    raise ValueError("Invalid mode or fan speed")
                encoded_temperature = temperature
                if mode == HVACMode.OFF and self.device.get("ignore_off_temperature") and self._previous:
                    encoded_temperature = self._previous.get("Temp", temperature)
                state = {**(self._previous or {}), **(extra or {}), "Power": mode != HVACMode.OFF, "Mode": "fan" if mode == HVACMode.FAN_ONLY else mode,
                         "Temp": encoded_temperature, "FanSpeed": fan}
                signal, state = await self.hub.hvac(self.device, state, self._previous)
            except (ValueError, TypeError, OverflowError) as err:
                raise HomeAssistantError(str(err)) from err
            await self.hub.send(self.device, signal)
            self._previous = state
            self._attr_hvac_mode, self._attr_target_temperature, self._attr_fan_mode = mode, temperature, fan
            if mode != HVACMode.OFF:
                self._last_active_mode = mode
            self.async_write_ha_state()
            self.hub.notify()

    async def async_set_temperature(self, **kwargs):
        await self._set(mode=kwargs.get("hvac_mode"), temperature=kwargs.get(ATTR_TEMPERATURE))

    async def async_set_hvac_mode(self, hvac_mode):
        await self._set(mode=hvac_mode)

    async def async_set_fan_mode(self, fan_mode):
        await self._set(fan=fan_mode)

    async def async_turn_on(self):
        mode = self._last_active_mode if self.device.get("keep_mode_on_power_on") else HVACMode(self.device.get("initial_hvac_mode", "auto"))
        if mode == HVACMode.OFF:
            mode = next(value for value in self.hvac_modes if value != HVACMode.OFF)
        await self._set(mode=mode)

    async def async_turn_off(self):
        await self._set(mode=HVACMode.OFF)

    async def async_set_preset_mode(self, preset_mode):
        if preset_mode not in ("none", "away") or not self.device.get("away_temp"):
            raise HomeAssistantError("Away preset is not enabled")
        if preset_mode == "away":
            self._pre_away_temperature = self.target_temperature
            self._attr_preset_mode = "away"
            await self._set(temperature=self.device["away_temp"])
        else:
            target = self._pre_away_temperature or self.device.get("initial_target_temp", self.target_temperature)
            self._attr_preset_mode = None
            await self._set(temperature=target)

    async def async_irhvac(self, command):
        try:
            command = normalize_hvac(command)
        except ValueError as err:
            raise HomeAssistantError(str(err)) from err
        allowed = {"Power", "Mode", "Temp", "FanSpeed", "SwingV", "SwingH", "Quiet", "Turbo", "Econo", "Light", "Filter", "Clean", "Beep", "iFeel", "Sleep", "Clock", "SensorTemp"}
        if set(command) - allowed:
            raise HomeAssistantError("Protocol and Model are configured on the device; unknown IRhvac fields")
        command = dict(command)
        mode = command.pop("Mode", None)
        if mode is not None:
            mode = {"fan":"fan_only", "heat/cool":"auto"}.get(str(mode).lower(), str(mode).lower())
        power = command.pop("Power", None)
        if power is not None and type(power) is not bool:
            raise HomeAssistantError("Power must be true or false")
        if power is False:
            mode = HVACMode.OFF
        elif power is True and mode is None and self.hvac_mode == HVACMode.OFF:
            mode = next(v for v in self.hvac_modes if v != HVACMode.OFF)
        temperature = command.pop("Temp", None)
        fan = command.pop("FanSpeed", None)
        if fan is not None:
            fan = str(fan).lower()
        await self._set(mode=mode, temperature=temperature, fan=fan, extra=command)
