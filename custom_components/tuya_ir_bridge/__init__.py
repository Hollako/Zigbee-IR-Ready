"""Zigbee IR Ready integration setup."""
import json
from pathlib import Path
from homeassistant.components import panel_custom, frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.helpers import config_validation as cv
from homeassistant.exceptions import ConfigEntryError
from .const import DOMAIN, PLATFORMS
from .hub import Hub
from .websocket_api import register_commands
from .services import register_services

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
_VERSION = json.loads((Path(__file__).parent / "manifest.json").read_text(encoding="utf-8"))["version"]
_CARD_URL = f"/{DOMAIN}_static/remote_card.js?v={_VERSION}"


async def async_setup(hass, config):
    register_commands(hass)
    register_services(hass)
    return True


async def async_setup_entry(hass, entry):
    try:
        hub = Hub(hass, entry)
        await hub.load()
    except (OSError, ValueError) as err:
        raise ConfigEntryError(f"Cannot start bundled IR engine: {err}") from err
    hass.data[DOMAIN] = hub
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    if not hass.data.get(f"{DOMAIN}_static"):
        await hass.http.async_register_static_paths([
            StaticPathConfig(f"/{DOMAIN}_static", str(Path(__file__).parent / "www"), False)
        ])
        hass.data[f"{DOMAIN}_static"] = True
    frontend.add_extra_js_url(hass, _CARD_URL)
    await panel_custom.async_register_panel(
        hass, webcomponent_name="zigbee-ir-ready-panel",
        sidebar_title="Zigbee IR Ready", sidebar_icon="mdi:remote",
        frontend_url_path="zigbee-ir-ready",
        module_url=f"/{DOMAIN}_static/manager.js?v={_VERSION}",
        embed_iframe=False, require_admin=True,
    )
    return True


async def async_unload_entry(hass, entry):
    await hass.data[DOMAIN].learning.close()
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False
    frontend.async_remove_panel(hass, "zigbee-ir-ready")
    frontend.remove_extra_js_url(hass, _CARD_URL)
    hass.data.pop(DOMAIN, None)
    return True
