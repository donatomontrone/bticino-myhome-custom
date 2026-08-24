"""BTicino MyHome integration using local OpenWebNet communication."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_GATEWAY_HOST, CONF_GATEWAY_PASSWORD, CONF_GATEWAY_PORT, DOMAIN, PLATFORMS
from .discovery import BticinoDiscovery, DiscoveredDevice
from .gateway import BticinoGateway, BticinoGatewayError

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class BticinoRuntimeData:
    """Runtime-only data for one BTicino config entry."""

    gateway: BticinoGateway
    devices: list[DiscoveredDevice]


BticinoConfigEntry = ConfigEntry[BticinoRuntimeData]


def _load_devices(entry: ConfigEntry) -> list[DiscoveredDevice]:
    return [DiscoveredDevice.from_dict(item) for item in entry.data.get("devices", [])]


async def async_setup_entry(hass: HomeAssistant, entry: BticinoConfigEntry) -> bool:
    data = entry.data
    gateway = BticinoGateway(
        host=data[CONF_GATEWAY_HOST],
        port=data[CONF_GATEWAY_PORT],
        password=data.get(CONF_GATEWAY_PASSWORD),
    )
    try:
        await gateway.async_connect(
            task_creator=lambda coro, name: entry.async_create_background_task(hass, coro, name)
        )
    except BticinoGatewayError as err:
        await gateway.async_close()
        raise ConfigEntryNotReady(str(err)) from err

    devices = _load_devices(entry)
    if not devices:
        try:
            discovery = BticinoDiscovery(gateway)
            devices = await discovery.async_run_full_scan(
                include_scenarios=entry.options.get("include_scenarios", True),
                listen_seconds=entry.options.get("discovery_listen_seconds", 3),
            )
            hass.config_entries.async_update_entry(
                entry, data={**entry.data, "devices": [d.to_dict() for d in devices]}
            )
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Discovery iniziale BTicino fallita")

    entry.runtime_data = BticinoRuntimeData(gateway=gateway, devices=devices)
    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception:
        await gateway.async_close()
        raise
    return True


async def async_unload_entry(hass: HomeAssistant, entry: BticinoConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.gateway.async_close()
    return unload_ok
