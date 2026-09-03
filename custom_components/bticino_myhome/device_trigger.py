"""Device triggers for BTicino MyHome scenarios."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_PLATFORM, CONF_TYPE
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .scene import BticinoScene


async def async_get_triggers(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, Any]]:
    """Return a list of triggers for a device."""
    from homeassistant.helpers.entity_platform import async_get_platforms

    triggers = []

    # Get all scene entities for this device
    platform = async_get_platforms(hass, DOMAIN)
    if not platform:
        return triggers

    for p in platform:
        for entity in p.entities.values():
            if isinstance(entity, BticinoScene) and entity.device_id == device_id:
                triggers.append({
                    CONF_DEVICE_ID: device_id,
                    CONF_DOMAIN: DOMAIN,
                    CONF_PLATFORM: "device",
                    CONF_TYPE: "scenario_activated",
                    "subtype": f"scenario_{entity.unique_id}",
                })

    return triggers


async def async_get_trigger_capabilities(
    hass: HomeAssistant, config: ConfigType
) -> dict[str, vol.Schema]:
    """Return trigger capabilities for a given configuration."""
    return {}
