"""Registry-backed virtual entity base. State is optimistic."""
import asyncio
from homeassistant.helpers.entity import Entity, DeviceInfo
from .const import DOMAIN


class IREntity(Entity):
    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_name = None
    _attr_assumed_state = True

    def __init__(self, hub, device):
        self.hub, self.device = hub, device
        self._command_lock = asyncio.Lock()
        self._attr_unique_id = device["id"]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device["id"])}, name=device["name"],
            manufacturer="Zigbee IR Ready", model=device["protocol"],
        )

    def apply_device(self, device):
        """Apply validated settings without replacing the registered entity."""
        self.device = device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device["id"])}, name=device["name"],
            manufacturer="Zigbee IR Ready", model=device["protocol"],
        )
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.hub.entities[self.entity_id] = self

    async def async_will_remove_from_hass(self):
        self.hub.entities.pop(self.entity_id, None)
        await super().async_will_remove_from_hass()

    async def send_command(self, name):
        from homeassistant.exceptions import HomeAssistantError
        async with self._command_lock:
            try:
                signal = await self.hub.command(self.device, name)
            except (KeyError, ValueError) as err:
                raise HomeAssistantError(f"Cannot encode {name}: {err}") from err
            await self.hub.send(self.device, signal)


def setup_platform(hass, entry, async_add_entities, kind, factory):
    hub = hass.data[DOMAIN]
    def add(device):
        async_add_entities([factory(hub, device)])
    hub.adders[kind] = add
    entry.async_on_unload(lambda: hub.adders.pop(kind, None))
    async_add_entities([factory(hub, d) for d in hub.devices if d["device_type"] == kind])
