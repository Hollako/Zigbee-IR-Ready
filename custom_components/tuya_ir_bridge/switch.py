"""Selectable feature switches sharing the climate's state and command lock."""
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.exceptions import HomeAssistantError
from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN]

    def add(device):
        entities = []
        for feature in device.get("feature_switches", []):
            key = (device["id"], feature)
            if key not in hub.feature_entities:
                entity = IRFeatureSwitch(hub, device, feature)
                hub.feature_entities[key] = entity
                entities.append(entity)
        if entities:
            async_add_entities(entities)
    hub.adders["switch"] = add
    entry.async_on_unload(lambda: hub.adders.pop("switch", None))
    for device in hub.devices:
        if device["device_type"] == "climate":
            add(device)


class IRFeatureSwitch(SwitchEntity):
    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_assumed_state = True

    def __init__(self, hub, device, feature):
        self.hub, self.device_id, self.feature = hub, device["id"], feature
        self._attr_unique_id = f"{self.device_id}_{feature}"
        self._attr_name = {"SwingV": "Vertical swing", "SwingH": "Horizontal swing"}.get(feature, feature)
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, self.device_id)})

    @property
    def climate(self):
        return self.hub.primary_entity(self.device_id)

    @property
    def available(self):
        return self.climate is not None and self.feature in self.climate.device.get("feature_switches", [])

    @property
    def is_on(self):
        if not self.available:
            return None
        state = {**self.climate.device.get("hvac_options", {}), **(self.climate._previous or {})}
        value = state.get(self.feature, -1 if self.feature == "Sleep" else False)
        if self.feature in ("SwingV", "SwingH"):
            return str(value).lower() not in ("off", "false")
        if self.feature == "Sleep":
            return value >= 0
        return bool(value)

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.hub.listeners.add(self.async_write_ha_state)
        self.async_on_remove(lambda: self.hub.listeners.discard(self.async_write_ha_state))

    async def async_turn_on(self, **kwargs):
        await self._set(True)

    async def async_turn_off(self, **kwargs):
        await self._set(False)

    async def _set(self, value):
        if not self.available:
            raise HomeAssistantError("Climate feature is unavailable")
        await self.climate.async_set_feature(self.feature, value)
