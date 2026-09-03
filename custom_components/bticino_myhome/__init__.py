"""BTicino MyHome integration using local OpenWebNet communication."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_GATEWAY_HOST, CONF_GATEWAY_PASSWORD, CONF_GATEWAY_PORT, DOMAIN, PLATFORMS
from .device import BticinoDeviceManager
from .discovery import DiscoveredDevice
from .gateway import BticinoGateway, BticinoGatewayError

_LOGGER = logging.getLogger(__name__)


@dataclass
class BticinoMyHomeData:
    gateway: BticinoGateway
    device_manager: BticinoDeviceManager


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BTicino MyHome from a config entry."""
    gateway = BticinoGateway(
        entry.data[CONF_GATEWAY_HOST],
        entry.data[CONF_GATEWAY_PORT],
        entry.data.get(CONF_GATEWAY_PASSWORD, ""),
    )
    try:
        await gateway.async_connect()
    except BticinoGatewayError as err:
        await gateway.async_close()
        raise ConfigEntryNotReady(f"Failed to connect to gateway: {err}") from err

    devices = [DiscoveredDevice.from_dict(d) for d in entry.data.get("devices", [])]
    device_manager = BticinoDeviceManager(devices)
    runtime = BticinoMyHomeData(gateway=gateway, device_manager=device_manager)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = runtime

    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        await gateway.async_close()
        raise

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry and release gateway resources."""
    data: BticinoMyHomeData = hass.data[DOMAIN][entry.entry_id]
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    await data.gateway.async_close()
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old config entries to the new format."""
    _LOGGER.debug("Migrating from version %s", entry.version)

    if entry.version == 1:
        new_data = {**entry.data}
        if "devices" not in new_data:
            new_data["devices"] = []

        hass.config_entries.async_update_entry(entry, data=new_data, version=2)
        _LOGGER.debug("Migration to version %s successful", entry.version)
        return True

    return True
