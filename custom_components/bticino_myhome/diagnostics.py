"""Diagnostics support for the BTicino MyHome integration."""
from __future__ import annotations

from typing import Any, cast

from homeassistant.core import HomeAssistant
from homeassistant.helpers.redact_data import async_redact_data

from .const import (
    CONF_GATEWAY_HOST,
    CONF_GATEWAY_ID,
    CONF_GATEWAY_PASSWORD,
    CONF_GATEWAY_UDN,
)
from .data import BticinoConfigEntry

TO_REDACT = {
    CONF_GATEWAY_PASSWORD,
    CONF_GATEWAY_HOST,
    CONF_GATEWAY_ID,
    CONF_GATEWAY_UDN,
    "udn",
    "uuid",
    "serial",
    "serialNumber",
    "mac",
    "macAddress",
    "name",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: BticinoConfigEntry
) -> dict[str, Any]:
    """Return safe diagnostics for a BTicino config entry."""
    runtime = entry.runtime_data
    gateway = runtime.gateway
    devices = runtime.device_manager.devices

    data = {
        "config_entry": {
            "entry_id": entry.entry_id,
            "version": entry.version,
            "minor_version": entry.minor_version,
        },
        "gateway": {
            "host": gateway.host,
            "port": gateway.port,
            "connected": gateway.connected,
            "command_connected": gateway.command_connected,
            "event_connected": gateway.event_connected,
        },
        "devices": [device.to_dict() for device in devices],
    }
    return cast(dict[str, Any], async_redact_data(data, TO_REDACT))
