"""BTicino MyHome integration using local OpenWebNet communication."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_GATEWAY_HOST, CONF_GATEWAY_PASSWORD, CONF_GATEWAY_PORT, DOMAIN as DOMAIN, PLATFORMS
from .device import BticinoDeviceManager
from .discovery import DiscoveredDevice
from .gateway import BticinoGateway, BticinoGatewayError

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class BticinoRuntimeData:
    """Runtime-only data for one BTicino config entry."""

    gateway: BticinoGateway
    device_manager: BticinoDeviceManager

    @property
    def devices(self) -> list[DiscoveredDevice]:
        """Return the current discovered device inventory."""
        return self.device_manager.devices


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
        _LOGGER.info(
            "Nessun dispositivo BTicino persistito: il gateway è pronto; "
            "avviare discovery/learning dalle opzioni dell'integrazione."
        )

    entry.runtime_data = BticinoRuntimeData(
        gateway=gateway, device_manager=BticinoDeviceManager(devices)
    )
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
