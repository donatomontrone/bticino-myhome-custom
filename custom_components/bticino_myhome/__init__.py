"""BTicino MyHome integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_GATEWAY_HOST, CONF_GATEWAY_PASSWORD, CONF_GATEWAY_PORT, DOMAIN, PLATFORMS
from .gateway import BticinoGateway, BticinoGatewayError
from .services import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BTicino MyHome from a config entry."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BTicino MyHome from a config entry."""
    # Setup services
    await async_setup_services(hass)

    # Create gateway
    gateway = BticinoGateway(
        host=entry.data[CONF_GATEWAY_HOST],
        port=entry.data[CONF_GATEWAY_PORT],
        password=entry.data[CONF_GATEWAY_PASSWORD],
    )

    try:
        await gateway.async_connect()
    except BticinoGatewayError as err:
        await gateway.async_close()
        raise ConfigEntryNotReady(f"Failed to connect to gateway: {err}") from err

    # Store runtime data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "gateway": gateway,
    }

    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Close gateway
    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id, None)
        if data and "gateway" in data:
            await data["gateway"].async_close()

    # Unload services if no more entries
    if not hass.data[DOMAIN]:
        await async_unload_services(hass)

    return unload_ok
