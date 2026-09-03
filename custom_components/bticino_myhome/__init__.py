"""BTicino MyHome integration using local OpenWebNet communication."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    CONF_GATEWAY_HOST,
    CONF_GATEWAY_PASSWORD,
    CONF_GATEWAY_PORT,
    DOMAIN,
    EVENT_OPENWEBNET,
    PLATFORMS,
)
from .device import BticinoDeviceManager
from .discovery import DiscoveredDevice
from .gateway import BticinoGateway, BticinoGatewayError
from .protocol import NormalizedEvent
from .services import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class BticinoMyHomeData:
    gateway: BticinoGateway
    device_manager: BticinoDeviceManager


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
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

    devices = [DiscoveredDevice.from_dict(data) for data in entry.data.get("devices", [])]
    runtime = BticinoMyHomeData(
        gateway=gateway,
        device_manager=BticinoDeviceManager(devices),
    )
    entry.runtime_data = runtime
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = runtime

    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        entry.runtime_data = None
        await gateway.async_close()
        raise

    def _forward_bus_event(event: NormalizedEvent) -> None:
        hass.bus.async_fire(
            EVENT_OPENWEBNET,
            {
                "who": event.who,
                "what": event.what,
                "where": event.where,
                "dimension": event.dimension,
                "values": list(event.values),
                "raw": event.raw,
            },
        )

    entry.async_on_unload(gateway.add_event_listener(_forward_bus_event))
    await async_setup_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    runtime = entry.runtime_data
    if runtime is None:
        return True
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unload_ok:
        return False

    await runtime.gateway.async_close()
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    entry.runtime_data = None
    if not hass.data.get(DOMAIN):
        await async_unload_services(hass)
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.debug("Migrating BTicino entry from version %s", entry.version)
    if entry.version == 1:
        new_data = {**entry.data}
        new_data.setdefault("devices", [])
        hass.config_entries.async_update_entry(entry, data=new_data, version=2)
    return True
