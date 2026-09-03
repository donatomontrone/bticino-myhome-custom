"""BTicino MyHome services."""
from __future__ import annotations

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN
from .gateway import BticinoGatewayError

SERVICE_SEND_FRAME = "send_frame"


async def async_setup_services(hass: HomeAssistant) -> None:
    """Register integration services once."""
    if hass.services.has_service(DOMAIN, SERVICE_SEND_FRAME):
        return

    async def handle_send_frame(call: ServiceCall) -> None:
        frame = str(call.data.get("frame", "")).strip()
        if not frame:
            raise HomeAssistantError("Frame is required")

        runtimes = list(hass.data.get(DOMAIN, {}).values())
        if not runtimes:
            raise HomeAssistantError("No gateway configured")
        gateway = runtimes[0].gateway
        try:
            await gateway.async_send(
                frame,
                is_status_request=bool(call.data.get("is_status_request", False)),
            )
        except BticinoGatewayError as err:
            raise HomeAssistantError(f"Failed to send frame: {err}") from err

    hass.services.async_register(DOMAIN, SERVICE_SEND_FRAME, handle_send_frame)


async def async_unload_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_SEND_FRAME):
        hass.services.async_remove(DOMAIN, SERVICE_SEND_FRAME)
