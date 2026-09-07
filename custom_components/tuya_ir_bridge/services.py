"""IRsend and IRhvac actions targeting existing integration entities."""
import voluptuous as vol
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.service import async_register_admin_service
from .const import DOMAIN


def register_services(hass):
    async def handle(call):
        hub = hass.data.get(DOMAIN)
        entity = hub.entities.get(call.data["entity_id"]) if hub else None
        if entity is None:
            raise HomeAssistantError("Select a loaded Zigbee IR Ready entity")
        try:
            if call.service == "irhvac":
                if not hasattr(entity, "async_irhvac"):
                    raise HomeAssistantError("IRhvac requires a climate entity")
                await entity.async_irhvac(call.data["command"])
            else:
                signal = await hub.irsend(entity.device, call.data["command"])
                await hub.send(entity.device, signal)
        except (ValueError, TypeError, KeyError) as err:
            raise HomeAssistantError(str(err)) from err

    for name in ("irsend", "irhvac"):
        schema = vol.Schema({vol.Required("entity_id"): cv.entity_id,
                             vol.Required("command"): vol.Any(dict, str) if name == "irsend" else dict})
        async_register_admin_service(hass, DOMAIN, name, handle, schema=schema)
