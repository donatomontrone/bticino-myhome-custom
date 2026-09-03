"""Tests for WHO=0 device triggers."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.bticino_myhome.const import DOMAIN, EVENT_OPENWEBNET
from custom_components.bticino_myhome.device_trigger import (
    CONF_SUBTYPE,
    TRIGGER_SCENARIO_ACTIVATED,
    async_attach_trigger,
    async_get_triggers,
)


def test_get_triggers_from_scene_device_identifier() -> None:
    async def scenario() -> None:
        registry = MagicMock()
        registry.async_get.return_value = SimpleNamespace(
            identifiers={(DOMAIN, "192.0.2.2:20000:0:12")}
        )
        with patch(
            "custom_components.bticino_myhome.device_trigger.dr.async_get",
            return_value=registry,
        ):
            triggers = await async_get_triggers(MagicMock(), "device-id")
        assert triggers[0]["type"] == TRIGGER_SCENARIO_ACTIVATED
        assert triggers[0][CONF_SUBTYPE] == "12"

    asyncio.run(scenario())


def test_attach_trigger_uses_standard_ha_event_trigger() -> None:
    async def scenario() -> None:
        action = MagicMock()
        trigger_info = MagicMock()
        with patch(
            "custom_components.bticino_myhome.device_trigger.event_trigger.async_attach_trigger",
            new=AsyncMock(return_value=MagicMock()),
        ) as attach:
            await async_attach_trigger(
                MagicMock(),
                {
                    "platform": "device",
                    "domain": DOMAIN,
                    "device_id": "device-id",
                    "type": TRIGGER_SCENARIO_ACTIVATED,
                    CONF_SUBTYPE: "12",
                },
                action,
                trigger_info,
            )
        event_config = attach.await_args.args[1]
        assert event_config["event_type"] == EVENT_OPENWEBNET
        assert event_config["event_data"] == {"who": "0", "where": "12"}

    asyncio.run(scenario())
