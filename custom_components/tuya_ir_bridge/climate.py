"""Climate using upstream IRac with per-device previous state."""
from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode
from homeassistant.const import UnitOfTemperature, ATTR_TEMPERATURE
from homeassistant.exceptions import HomeAssistantError
from .entity import IREntity, setup_platform
from homeassistant.helpers.restore_state import RestoreEntity
from .commands import normalize_hvac


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
        self._attr_min_temp = device.get("min_temp", 16)
        self._attr_max_temp = device.get("max_temp", 32 if device["protocol"].lower() in ("electra", "electra_ac") else 30)
        self._attr_target_temperature_step = device.get("temp_step", 1)
        self._attr_target_temperature = max(self._attr_min_temp, min(24, self._attr_max_temp))

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last:
            self._previous = last.attributes.get("ir_previous_state")
            if last.state in self._attr_hvac_modes:
                self._attr_hvac_mode = HVACMode(last.state)
            self._attr_target_temperature = last.attributes.get("temperature", 24)
            self._attr_fan_mode = last.attributes.get("fan_mode", "auto")

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
        super().apply_device(device)

    async def _set(self, mode=None, temperature=None, fan=None, extra=None):
        async with self._command_lock:
            mode = self._attr_hvac_mode if mode is None else mode
            temperature = self._attr_target_temperature if temperature is None else temperature
            fan = self._attr_fan_mode if fan is None else fan
            try:
                if isinstance(temperature, bool) or not self.min_temp <= temperature <= self.max_temp:
                    raise ValueError("Temperature outside configured device range")
                if mode not in self.hvac_modes or fan not in self.fan_modes:
                    raise ValueError("Invalid mode or fan speed")
                state = {**(self._previous or {}), **(extra or {}), "Power": mode != HVACMode.OFF, "Mode": "fan" if mode == HVACMode.FAN_ONLY else mode,
                         "Temp": temperature, "FanSpeed": fan}
                signal, state = await self.hub.hvac(self.device, state, self._previous)
            except (ValueError, TypeError, OverflowError) as err:
                raise HomeAssistantError(str(err)) from err
            await self.hub.send(self.device, signal)
            self._previous = state
            self._attr_hvac_mode, self._attr_target_temperature, self._attr_fan_mode = mode, temperature, fan
            self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs):
        await self._set(mode=kwargs.get("hvac_mode"), temperature=kwargs.get(ATTR_TEMPERATURE))

    async def async_set_hvac_mode(self, hvac_mode):
        await self._set(mode=hvac_mode)

    async def async_set_fan_mode(self, fan_mode):
        await self._set(fan=fan_mode)

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
            mode = HVACMode.AUTO
        temperature = command.pop("Temp", None)
        fan = command.pop("FanSpeed", None)
        if fan is not None:
            fan = str(fan).lower()
        await self._set(mode=mode, temperature=temperature, fan=fan, extra=command)
