"""BTicino MyHome services."""
from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN
from .gateway import BticinoGateway, BticinoGatewayError

_LOGGER = logging.getLogger(__name__)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for BTicino MyHome."""

    async def handle_send_frame(call: ServiceCall) -> None:
        """Handle send_frame service call."""
        frame = call.data.get("frame")
        is_status_request = call.data.get("is_status_request", False)

        if not frame:
            raise HomeAssistantError("Frame is required")

        # Get gateway from config entries
        gateways: list[BticinoGateway] = []
        for entry in hass.config_entries.async_entries(DOMAIN):
            if entry.data.get("gateway"):
                gateways.append(hass.data[DOMAIN][entry.entry_id].gateway)

        if not gateways:
            raise HomeAssistantError("No gateway configured")

        # Send frame to first gateway (could be extended to support multiple)
        gateway = gateways[0]
        try:
            await gateway.async_send(frame, is_status_request=is_status_request)
            _LOGGER.debug("Sent frame: %s", frame)
        except BticinoGatewayError as err:
            raise HomeAssistantError(f"Failed to send frame: {err}") from err

    hass.services.async_register(
        DOMAIN,
        "send_frame",
        handle_send_frame,
    )


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload services for BTicino MyHome."""
    hass.services.async_remove(DOMAIN, "send_frame")
