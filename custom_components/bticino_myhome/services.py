"""BTicino MyHome integration-wide actions."""
from __future__ import annotations

from typing import cast

import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .data import BticinoConfigEntry
from .gateway import BticinoGateway, BticinoGatewayError
from .protocol.alarm import alarm_arm_partitions

SERVICE_SEND_FRAME = "send_frame"
SERVICE_ARM_ALARM_PARTITIONS = "arm_alarm_partitions"
ATTR_CONFIG_ENTRY_ID = "config_entry_id"
ATTR_FRAME = "frame"
ATTR_IS_STATUS_REQUEST = "is_status_request"
ATTR_PARTITIONS = "partitions"

SERVICE_SEND_FRAME_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CONFIG_ENTRY_ID): cv.string,
        vol.Required(ATTR_FRAME): cv.string,
        vol.Optional(ATTR_IS_STATUS_REQUEST, default=False): cv.boolean,
    }
)

SERVICE_ARM_ALARM_PARTITIONS_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CONFIG_ENTRY_ID): cv.string,
        vol.Required(ATTR_PARTITIONS): vol.All(cv.ensure_list, [vol.Coerce(int)]),
    }
)


def _loaded_gateway(hass: HomeAssistant, entry_id: str) -> BticinoGateway:
    entry = hass.config_entries.async_get_entry(entry_id)
    if entry is None or entry.domain != DOMAIN:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="send_frame_entry_not_found",
        )
    if entry.state is not ConfigEntryState.LOADED:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="send_frame_entry_not_loaded",
        )
    return cast(BticinoConfigEntry, entry).runtime_data.gateway


async def async_setup_services(hass: HomeAssistant) -> None:
    """Register integration actions once from integration setup."""

    if not hass.services.has_service(DOMAIN, SERVICE_SEND_FRAME):

        async def handle_send_frame(call: ServiceCall) -> None:
            entry_id = str(call.data.get(ATTR_CONFIG_ENTRY_ID, "")).strip()
            frame = str(call.data.get(ATTR_FRAME, "")).strip()
            if not frame:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="send_frame_missing_frame",
                )

            gateway = _loaded_gateway(hass, entry_id)
            try:
                await gateway.async_send(
                    frame,
                    is_status_request=bool(
                        call.data.get(ATTR_IS_STATUS_REQUEST, False)
                    ),
                )
            except BticinoGatewayError as err:
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="send_frame_failed",
                    translation_placeholders={"detail": str(err)},
                ) from err

        hass.services.async_register(
            DOMAIN,
            SERVICE_SEND_FRAME,
            handle_send_frame,
            schema=SERVICE_SEND_FRAME_SCHEMA,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_ARM_ALARM_PARTITIONS):

        async def handle_arm_alarm_partitions(call: ServiceCall) -> None:
            entry_id = str(call.data.get(ATTR_CONFIG_ENTRY_ID, "")).strip()
            try:
                frame = alarm_arm_partitions(call.data.get(ATTR_PARTITIONS, []))
            except ValueError as err:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="alarm_partitions_invalid",
                    translation_placeholders={"detail": str(err)},
                ) from err

            gateway = _loaded_gateway(hass, entry_id)
            try:
                await gateway.async_send(frame)
            except BticinoGatewayError as err:
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="entity_command_failed",
                    translation_placeholders={"detail": str(err)},
                ) from err

        hass.services.async_register(
            DOMAIN,
            SERVICE_ARM_ALARM_PARTITIONS,
            handle_arm_alarm_partitions,
            schema=SERVICE_ARM_ALARM_PARTITIONS_SCHEMA,
        )
