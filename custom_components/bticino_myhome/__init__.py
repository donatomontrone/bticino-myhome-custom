"""BTicino MyHome integration using local OpenWebNet communication."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

from .const import (
    CONF_DEVICES,
    CONF_GATEWAY_FIRMWARE,
    CONF_GATEWAY_HOST,
    CONF_GATEWAY_ID,
    CONF_GATEWAY_MANUFACTURER,
    CONF_GATEWAY_MODEL,
    CONF_GATEWAY_PASSWORD,
    CONF_GATEWAY_PORT,
    CONF_GATEWAY_SERIAL,
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
    gateway_identity = str(entry.data.get(CONF_GATEWAY_ID) or entry.unique_id or f"{entry.data[CONF_GATEWAY_HOST]}:{entry.data[CONF_GATEWAY_PORT]}")
    gateway = BticinoGateway(
        entry.data[CONF_GATEWAY_HOST],
        entry.data[CONF_GATEWAY_PORT],
        entry.data.get(CONF_GATEWAY_PASSWORD, ""),
        identity=gateway_identity,
    )
    try:
        await gateway.async_connect(lambda coroutine, name: hass.async_create_task(coroutine, name))
    except BticinoGatewayError as err:
        await gateway.async_close()
        raise ConfigEntryNotReady(f"Failed to connect to gateway: {err}") from err

    devices = [DiscoveredDevice.from_dict(data) for data in entry.data.get(CONF_DEVICES, [])]
    runtime = BticinoMyHomeData(gateway=gateway, device_manager=BticinoDeviceManager(devices))
    entry.runtime_data = runtime
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = runtime

    dev_reg = dr.async_get(hass)
    dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, gateway.identity)},
        name=entry.title or "BTicino MyHome MH201",
        manufacturer=entry.data.get(CONF_GATEWAY_MANUFACTURER, "BTicino / Legrand"),
        model=entry.data.get(CONF_GATEWAY_MODEL, "MH201"),
        serial_number=entry.data.get(CONF_GATEWAY_SERIAL),
        sw_version=entry.data.get(CONF_GATEWAY_FIRMWARE),
    )

    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        entry.runtime_data = None
        await gateway.async_close()
        raise

    def _forward_bus_event(event: NormalizedEvent) -> None:
        hass.bus.async_fire(EVENT_OPENWEBNET, {
            "who": event.who,
            "what": event.what,
            "where": event.where,
            "dimension": event.dimension,
            "values": list(event.values),
            "raw": event.raw,
        })

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
    if entry.version >= 3:
        return True
    new_data = {**entry.data}
    new_data.setdefault(CONF_DEVICES, [])
    new_data.setdefault(CONF_GATEWAY_ID, entry.unique_id or f"{entry.data[CONF_GATEWAY_HOST]}:{entry.data[CONF_GATEWAY_PORT]}")
    hass.config_entries.async_update_entry(entry, data=new_data, version=3)
    return True
