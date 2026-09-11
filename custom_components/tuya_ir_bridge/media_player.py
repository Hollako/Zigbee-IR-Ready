"""IR media player with explicit power commands."""
from homeassistant.components.media_player import MediaPlayerEntity, MediaPlayerEntityFeature, MediaPlayerState
from .entity import IREntity, setup_platform

SOURCE_CYCLE_OPTION = "Input"


async def async_setup_entry(hass, entry, async_add_entities):
    setup_platform(hass, entry, async_add_entities, "media_player", IRMediaPlayer)


class IRMediaPlayer(IREntity, MediaPlayerEntity):
    _attr_supported_features = MediaPlayerEntityFeature.TURN_ON | MediaPlayerEntityFeature.TURN_OFF

    @property
    def supported_features(self):
        features = MediaPlayerEntityFeature.TURN_ON | MediaPlayerEntityFeature.TURN_OFF
        commands = self.device.get('commands', {})
        for name, feature in [('play', 'PLAY'), ('pause', 'PAUSE'), ('stop', 'STOP'), ('next', 'NEXT_TRACK'), ('previous', 'PREVIOUS_TRACK'), ('mute', 'VOLUME_MUTE')]:
            if name in commands:
                features |= getattr(MediaPlayerEntityFeature, feature)
        if {'volume_up', 'volume_down'} <= commands.keys():
            features |= MediaPlayerEntityFeature.VOLUME_STEP
        if self.source_list:
            features |= MediaPlayerEntityFeature.SELECT_SOURCE
        return features

    @property
    def source_list(self):
        commands = self.device.get('commands', {})
        direct = [key[7:] for key in commands if key.startswith('source:')]
        if 'source_cycle' not in commands:
            return direct
        return [SOURCE_CYCLE_OPTION, *[source for source in direct if source != SOURCE_CYCLE_OPTION]]

    async def async_select_source(self, source):
        if source == SOURCE_CYCLE_OPTION and 'source_cycle' in self.device.get('commands', {}):
            await self.send_command('source_cycle')
            # A cycle command does not reveal the resulting input. Clearing the
            # optimistic value also lets Home Assistant select Input repeatedly.
            self._attr_source = None
            self.async_write_ha_state()
            return
        await self.send_command('source:' + source)
        self._attr_source = source
        self.async_write_ha_state()

    async def async_volume_up(self):
        await self.send_command('volume_up')

    async def async_volume_down(self):
        await self.send_command('volume_down')

    async def async_mute_volume(self, mute):
        if self.is_volume_muted != mute:
            await self.send_command('mute')
            self._attr_is_volume_muted = mute
            self.async_write_ha_state()

    async def async_media_play(self):
        await self.send_command('play')
        self._attr_state = MediaPlayerState.PLAYING
        self.async_write_ha_state()

    async def async_media_pause(self):
        await self.send_command('pause')
        self._attr_state = MediaPlayerState.PAUSED
        self.async_write_ha_state()

    async def async_media_stop(self):
        await self.send_command('stop')
        self._attr_state = MediaPlayerState.IDLE
        self.async_write_ha_state()

    async def async_media_next_track(self):
        await self.send_command('next')

    async def async_media_previous_track(self):
        await self.send_command('previous')

    async def async_turn_on(self):
        await self.send_command("turn_on")
        self._attr_state = MediaPlayerState.ON
        self.async_write_ha_state()

    async def async_turn_off(self):
        await self.send_command("turn_off")
        self._attr_state = MediaPlayerState.OFF
        self.async_write_ha_state()
