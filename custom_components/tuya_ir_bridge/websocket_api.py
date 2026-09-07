"""Admin-only panel API; registry population is handled by entity platforms."""
import voluptuous as vol
from homeassistant.components import websocket_api
from .const import DOMAIN


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/list"})
@websocket_api.async_response
async def list_devices(hass, connection, msg):
    connection.require_admin()
    hub = hass.data.get(DOMAIN)
    if hub is None:
        connection.send_error(msg["id"], "not_loaded", "Integration is not loaded")
        return
    connection.send_result(msg["id"], hub.devices)


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/create", vol.Required("device"): dict})
@websocket_api.async_response
async def create_device(hass, connection, msg):
    connection.require_admin()
    hub = hass.data.get(DOMAIN)
    if hub is None:
        connection.send_error(msg["id"], "not_loaded", "Integration is not loaded")
        return
    try:
        device = await hub.create(msg["device"])
    except ValueError as err:
        connection.send_error(msg["id"], "invalid_device", str(err))
        return
    connection.send_result(msg["id"], device)


def register_commands(hass):
    websocket_api.async_register_command(hass, list_devices)
    websocket_api.async_register_command(hass, create_device)
