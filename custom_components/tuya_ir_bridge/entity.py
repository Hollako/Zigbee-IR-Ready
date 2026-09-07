"""Registry-backed virtual entity base. State is optimistic."""
from homeassistant.helpers.entity import Entity, DeviceInfo
from .const import DOMAIN
from .protocols import encode_command


class IREntity(Entity):
    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_name = None
    _attr_assumed_state = True

    def __init__(self, hub, device):
        self.hub, self.device = hub, device
        self._attr_unique_id = device["id"]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device["id"])}, name=device["name"],
            manufacturer="Zigbee IR Ready", model=device["protocol"],
        )

    async def send_command(self, name):
        from homeassistant.exceptions import HomeAssistantError
        try:
            command = self.device.get("commands", {})[name]
            raw = encode_command(self.device["protocol"], self.device.get("address", 0), command)
        except (KeyError, ValueError) as err:
            raise HomeAssistantError(f"Unsupported command: {name}") from err
        await self.hub.send(self.device, raw)


def setup_platform(hass, entry, async_add_entities, kind, factory):
    hub = hass.data[DOMAIN]
    def add(device):
        async_add_entities([factory(hub, device)])
    hub.adders[kind] = add
    entry.async_on_unload(lambda: hub.adders.pop(kind, None))
    async_add_entities([factory(hub, d) for d in hub.devices if d["device_type"] == kind])
