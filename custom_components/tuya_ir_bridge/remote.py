"""Protocol-driven remote entity."""
import asyncio
from homeassistant.components.remote import RemoteEntity
from homeassistant.exceptions import HomeAssistantError
from .entity import IREntity, setup_platform


async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data['tuya_ir_bridge']
    def add(device):
        async_add_entities([IRRemote(hub, device)])
    hub.adders['remote'] = add
    entry.async_on_unload(lambda: hub.adders.pop('remote', None))
    async_add_entities([IRRemote(hub, d) for d in hub.devices if d['device_type'] in ('remote', 'media_player')])


class IRRemote(IREntity, RemoteEntity):
    _attr_is_on = True

    def __init__(self, hub, device):
        super().__init__(hub, device)
        if device['device_type'] == 'media_player':
            self._attr_unique_id = device['id'] + '_remote'
            self._attr_name = 'Remote'

    @property
    def extra_state_attributes(self):
        aliases = {'turn_on': 'power_on', 'turn_off': 'power_off'}
        names = [key[7:] if key.startswith('source:') else aliases.get(key, key) for key in self.device.get('commands', {})]
        return {'configured_commands': names, 'source_list': [key[7:] for key in self.device.get('commands', {}) if key.startswith('source:')], 'zigbee_ir_device_id': self.device['id']}

    async def send_command(self, name):
        name = {'power_on': 'turn_on', 'power_off': 'turn_off'}.get(name, name)
        if name not in self.device.get('commands', {}) and 'source:' + name in self.device.get('commands', {}):
            name = 'source:' + name
        if self.device['device_type'] == 'media_player':
            primary = self.hub.primary_entity(self.device['id'])
            if primary is not None and primary is not self:
                return await primary.send_command(name)
        await super().send_command(name)

    async def async_send_command(self, command, **kwargs):
        repeats = kwargs.get("num_repeats", 1)
        delay = kwargs.get("delay_secs", 0.1)
        if not 1 <= repeats <= 10 or not 0 <= delay <= 10 or kwargs.get("hold_secs", 0):
            raise HomeAssistantError("Use 1..10 repeats, delay 0..10, and no hold")
        if isinstance(command, str):
            command = [command]
        for _ in range(repeats):
            for name in command:
                await self.send_command(name)
                await asyncio.sleep(delay)
