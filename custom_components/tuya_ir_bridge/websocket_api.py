"""Admin-only panel API; registry population is handled by entity platforms."""
import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.exceptions import Unauthorized, HomeAssistantError
from .const import DOMAIN


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/list"})
@websocket_api.async_response
async def list_devices(hass, connection, msg):
    if connection.user is None or not connection.user.is_admin:
        raise Unauthorized
    hub = hass.data.get(DOMAIN)
    if hub is None:
        connection.send_error(msg["id"], "not_loaded", "Integration is not loaded")
        return
    connection.send_result(msg["id"], hub.devices)


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/create", vol.Required("device"): dict})
@websocket_api.async_response
async def create_device(hass, connection, msg):
    if connection.user is None or not connection.user.is_admin:
        raise Unauthorized
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
    websocket_api.async_register_command(hass, catalogue)
    websocket_api.async_register_command(hass, update_device)
    websocket_api.async_register_command(hass, panel_action)
    websocket_api.async_register_command(hass, delete_device)


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/delete", vol.Required("device_id"): str})
@websocket_api.async_response
async def delete_device(hass, connection, msg):
    if connection.user is None or not connection.user.is_admin:
        raise Unauthorized
    hub = hass.data.get(DOMAIN)
    if hub is None:
        connection.send_error(msg["id"], "not_loaded", "Integration is not loaded")
        return
    try:
        result = await hub.delete(msg["device_id"])
    except (ValueError, OSError) as err:
        connection.send_error(msg["id"], "delete_failed", str(err))
        return
    connection.send_result(msg["id"], result)


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/update", vol.Required("device_id"): str, vol.Required("device"): dict})
@websocket_api.async_response
async def update_device(hass, connection, msg):
    if connection.user is None or not connection.user.is_admin:
        raise Unauthorized
    hub = hass.data.get(DOMAIN)
    if hub is None:
        connection.send_error(msg["id"], "not_loaded", "Integration is not loaded")
        return
    try:
        device = await hub.update(msg["device_id"], msg["device"])
    except ValueError as err:
        connection.send_error(msg["id"], "invalid_device", str(err))
        return
    connection.send_result(msg["id"], device)


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/catalogue"})
@websocket_api.async_response
async def catalogue(hass, connection, msg):
    if connection.user is None or not connection.user.is_admin:
        raise Unauthorized
    hub = hass.data.get(DOMAIN)
    if hub is None:
        connection.send_error(msg["id"], "not_loaded", "Integration is not loaded")
        return
    connection.send_result(msg["id"], hub.catalogue)


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/action", vol.Required("action"): str, vol.Optional("data", default={}): dict})
@websocket_api.async_response
async def panel_action(hass, connection, msg):
    if connection.user is None or not connection.user.is_admin:
        raise Unauthorized
    hub = hass.data.get(DOMAIN)
    if hub is None:
        connection.send_error(msg["id"], "not_loaded", "Integration is not loaded")
        return
    data = msg.get("data", {})
    try:
        action = msg['action']
        if action == 'learn_start':
            result = await hub.learning.start(data['topic'])
        elif action == 'learn_status':
            result = hub.learning.status(data['session'])
        elif action == 'learn_cancel':
            await hub.learning.cancel(data['session'])
            result = {}
        elif action == 'test':
            from .hub import validate_device
            device = validate_device(data['device'], hub.catalogue)
            signal = await hub.command(device, data['command'])
            await hub.send(device, signal)
            result = {}
        elif action == 'remote':
            entity = hub.primary_entity(data['device_id'])
            if entity is None or entity.device['device_type'] == 'climate':
                raise ValueError('Select a loaded remote or media device')
            await entity.send_command(data['command'])
            result = {}
        elif action == 'feature':
            entity = hub.primary_entity(data['device_id'])
            if entity is None or not hasattr(entity, 'async_set_feature') or type(data['enabled']) is not bool:
                raise ValueError('Select a loaded climate and a boolean state')
            await entity.async_set_feature(data['feature'], data['enabled'])
            result = {}
        else:
            raise ValueError('Unknown panel action')
    except (ValueError, KeyError, TypeError, HomeAssistantError) as err:
        connection.send_error(msg['id'], 'invalid_action', str(err))
        return
    connection.send_result(msg['id'], result)
