"""Protocol-driven remote entity."""
import asyncio
from homeassistant.components.remote import RemoteEntity
from homeassistant.exceptions import HomeAssistantError
from .entity import IREntity, setup_platform


async def async_setup_entry(hass, entry, async_add_entities):
    setup_platform(hass, entry, async_add_entities, "remote", IRRemote)


class IRRemote(IREntity, RemoteEntity):
    _attr_is_on = True

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
