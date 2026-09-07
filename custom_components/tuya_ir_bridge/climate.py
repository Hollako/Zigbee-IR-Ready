"""Experimental Electra climate state encoder."""
import asyncio
from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode
from homeassistant.const import UnitOfTemperature, ATTR_TEMPERATURE
from homeassistant.exceptions import HomeAssistantError
from .entity import IREntity, setup_platform
from .protocols import encode_electra


async def async_setup_entry(hass, entry, async_add_entities):
    setup_platform(hass, entry, async_add_entities, "climate", IRClimate)


class IRClimate(IREntity, ClimateEntity):
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp, _attr_max_temp = 16, 32
    _attr_target_temperature_step = 1
    _attr_target_temperature = 24
    _attr_hvac_mode = HVACMode.OFF
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.AUTO, HVACMode.COOL, HVACMode.HEAT, HVACMode.DRY, HVACMode.FAN_ONLY]
    _attr_fan_mode = "auto"
    _attr_fan_modes = ["auto", "low", "medium", "high"]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE

    def __init__(self, hub, device):
        super().__init__(hub, device)
        self._command_lock = asyncio.Lock()

    async def _set(self, mode=None, temperature=None, fan=None):
        async with self._command_lock:
            mode = self._attr_hvac_mode if mode is None else mode
            temperature = self._attr_target_temperature if temperature is None else temperature
            fan = self._attr_fan_mode if fan is None else fan
            try:
                if isinstance(temperature, bool) or int(temperature) != temperature:
                    raise ValueError("Use whole-degree temperatures")
                raw = encode_electra(mode, int(temperature), fan)
            except (ValueError, TypeError, OverflowError) as err:
                raise HomeAssistantError(str(err)) from err
            await self.hub.send(self.device, raw)
            self._attr_hvac_mode, self._attr_target_temperature, self._attr_fan_mode = mode, temperature, fan
            self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs):
        await self._set(mode=kwargs.get("hvac_mode"), temperature=kwargs.get(ATTR_TEMPERATURE))

    async def async_set_hvac_mode(self, hvac_mode):
        await self._set(mode=hvac_mode)

    async def async_set_fan_mode(self, fan_mode):
        await self._set(fan=fan_mode)
