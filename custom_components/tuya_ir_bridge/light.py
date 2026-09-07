"""On/off IR light."""
from homeassistant.components.light import LightEntity, ColorMode
from .entity import IREntity, setup_platform


async def async_setup_entry(hass, entry, async_add_entities):
    setup_platform(hass, entry, async_add_entities, "light", IRLight)


class IRLight(IREntity, LightEntity):
    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}
    _attr_is_on = None

    async def async_turn_on(self, **kwargs):
        await self.send_command("turn_on")
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        await self.send_command("turn_off")
        self._attr_is_on = False
        self.async_write_ha_state()
