"""BTicino MyHome integration using local OpenWebNet communication."""
from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.typing import ConfigType

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
from .data import BticinoConfigEntry, BticinoMyHomeData
from .device import BticinoDeviceManager
from .discovery import DiscoveredDevice
from .gateway import (
    BticinoGateway,
    BticinoGatewayAuthError,
    BticinoGatewayError,
)
from .protocol import NormalizedEvent
from .services import async_setup_services

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up integration-wide actions independently from config entries."""
    await async_setup_services(hass)
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: BticinoConfigEntry
) -> bool:
    gateway_identity = str(
        entry.data.get(CONF_GATEWAY_ID)
        or entry.unique_id
        or f"{entry.data[CONF_GATEWAY_HOST]}:{entry.data[CONF_GATEWAY_PORT]}"
    )
    gateway = BticinoGateway(
        entry.data[CONF_GATEWAY_HOST],
        entry.data[CONF_GATEWAY_PORT],
        entry.data.get(CONF_GATEWAY_PASSWORD, ""),
        identity=gateway_identity,
    )
    try:
        await gateway.async_connect(
            lambda coroutine, name: hass.async_create_task(coroutine, name)
        )
    except BticinoGatewayAuthError as err:
        await gateway.async_close()
        raise ConfigEntryAuthFailed(
            f"Authentication rejected by gateway: {err}"
        ) from err
    except BticinoGatewayError as err:
        await gateway.async_close()
        raise ConfigEntryNotReady(
            f"Failed to connect to gateway: {err}"
        ) from err

    devices = [
        DiscoveredDevice.from_dict(data)
        for data in entry.data.get(CONF_DEVICES, [])
    ]
    runtime = BticinoMyHomeData(
        gateway=gateway,
        device_manager=BticinoDeviceManager(devices),
    )
    entry.runtime_data = runtime
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = runtime

    dev_reg = dr.async_get(hass)
    dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, gateway.identity)},
        name=entry.title or "BTicino MyHome MH201",
        manufacturer=entry.data.get(
            CONF_GATEWAY_MANUFACTURER, "BTicino / Legrand"
        ),
        model=entry.data.get(CONF_GATEWAY_MODEL, "MH201"),
        serial_number=entry.data.get(CONF_GATEWAY_SERIAL),
        sw_version=entry.data.get(CONF_GATEWAY_FIRMWARE),
    )

    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception:
        hass.data[DOMAIN].pop(entry.entry_id, None)
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
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: BticinoConfigEntry
) -> bool:
    runtime = getattr(entry, "runtime_data", None)
    if runtime is None:
        return True
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    )
    if not unload_ok:
        return False
    await runtime.gateway.async_close()
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return True


async def async_remove_config_entry_device(
    hass: HomeAssistant,
    config_entry: BticinoConfigEntry,
    device_entry: DeviceEntry,
) -> bool:
    """Remove an inventory endpoint after an explicit HA device removal."""
    runtime = getattr(config_entry, "runtime_data", None)
    if runtime is None:
        return False
    key = _device_key_from_registry_entry(
        device_entry, runtime.gateway.identity
    )
    if key is None or not runtime.device_manager.remove(key):
        return False
    hass.config_entries.async_update_entry(
        config_entry,
        data={
            **config_entry.data,
            CONF_DEVICES: runtime.device_manager.as_dicts(),
        },
    )
    return True


def _device_key_from_registry_entry(
    device_entry: DeviceEntry, gateway_identity: str
) -> str | None:
    for domain, identifier in device_entry.identifiers:
        if domain != DOMAIN:
            continue
        parts = identifier.rsplit(":", 2)
        if len(parts) != 3 or parts[0] != gateway_identity:
            continue
        return f"{parts[1]}-{parts[2]}"
    return None


async def async_migrate_entry(
    hass: HomeAssistant, entry: BticinoConfigEntry
) -> bool:
    _LOGGER.debug(
        "Migrating BTicino entry from version %s", entry.version
    )
    if entry.version >= 3:
        return True
    new_data = {**entry.data}
    new_data.setdefault(CONF_DEVICES, [])
    new_data.setdefault(
        CONF_GATEWAY_ID,
        entry.unique_id
        or f"{entry.data[CONF_GATEWAY_HOST]}:{entry.data[CONF_GATEWAY_PORT]}",
    )
    hass.config_entries.async_update_entry(
        entry, data=new_data, version=3
    )
    return True
