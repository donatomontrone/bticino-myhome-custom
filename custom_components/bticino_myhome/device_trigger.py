"""Device triggers for BTicino MyHome scenario events."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components.device_automation import DEVICE_TRIGGER_BASE_SCHEMA
from homeassistant.components.homeassistant.triggers import event as event_trigger
from homeassistant.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_PLATFORM, CONF_TYPE
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.trigger import TriggerActionType, TriggerInfo
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, EVENT_OPENWEBNET, WHO_SCENARIO

CONF_SUBTYPE = "subtype"
TRIGGER_SCENARIO_ACTIVATED = "scenario_activated"

TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In({TRIGGER_SCENARIO_ACTIVATED}),
        vol.Required(CONF_SUBTYPE): str,
    }
)


async def async_get_triggers(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, Any]]:
    """Return scenario triggers for a registered WHO=0 endpoint."""
    device = dr.async_get(hass).async_get(device_id)
    if device is None:
        return []

    triggers: list[dict[str, Any]] = []
    for domain, identifier in device.identifiers:
        if domain != DOMAIN:
            continue
        parts = identifier.rsplit(":", 2)
        if len(parts) != 3 or parts[-2] != WHO_SCENARIO:
            continue
        where = parts[-1]
        triggers.append(
            {
                CONF_PLATFORM: "device",
                CONF_DOMAIN: DOMAIN,
                CONF_DEVICE_ID: device_id,
                CONF_TYPE: TRIGGER_SCENARIO_ACTIVATED,
                CONF_SUBTYPE: where,
            }
        )
    return triggers


async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action: TriggerActionType,
    trigger_info: TriggerInfo,
) -> CALLBACK_TYPE:
    """Attach a scenario event trigger using Home Assistant's event helper."""
    event_config = event_trigger.TRIGGER_SCHEMA(
        {
            event_trigger.CONF_PLATFORM: "event",
            event_trigger.CONF_EVENT_TYPE: EVENT_OPENWEBNET,
            event_trigger.CONF_EVENT_DATA: {
                "who": WHO_SCENARIO,
                "where": config[CONF_SUBTYPE],
            },
        }
    )
    return await event_trigger.async_attach_trigger(
        hass,
        event_config,
        action,
        trigger_info,
        platform_type="device",
    )


async def async_get_trigger_capabilities(
    hass: HomeAssistant, config: ConfigType
) -> dict[str, vol.Schema]:
    return {}
