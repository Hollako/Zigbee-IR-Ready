"""IR media player with explicit power commands."""
from homeassistant.components.media_player import MediaPlayerEntity, MediaPlayerEntityFeature, MediaPlayerState
from .entity import IREntity, setup_platform


async def async_setup_entry(hass, entry, async_add_entities):
    setup_platform(hass, entry, async_add_entities, "media_player", IRMediaPlayer)


class IRMediaPlayer(IREntity, MediaPlayerEntity):
    _attr_supported_features = MediaPlayerEntityFeature.TURN_ON | MediaPlayerEntityFeature.TURN_OFF

    async def async_turn_on(self):
        await self.send_command("turn_on")
        self._attr_state = MediaPlayerState.ON
        self.async_write_ha_state()

    async def async_turn_off(self):
        await self.send_command("turn_off")
        self._attr_state = MediaPlayerState.OFF
        self.async_write_ha_state()
