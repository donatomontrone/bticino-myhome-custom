"""Tests for BTicino MyHome integration-wide actions."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from custom_components.bticino_myhome.const import DOMAIN
from custom_components.bticino_myhome.gateway import BticinoGatewayError
from custom_components.bticino_myhome.services import (
    ATTR_CONFIG_ENTRY_ID,
    ATTR_PARTITIONS,
    SERVICE_ARM_ALARM_PARTITIONS,
    SERVICE_SEND_FRAME,
    async_setup_services,
)


class _Services:
    def __init__(self) -> None:
        self.handlers = {}
        self.schemas = {}

    def has_service(self, domain: str, service: str) -> bool:
        return (domain, service) in self.handlers

    def async_register(self, domain: str, service: str, handler, *, schema=None) -> None:
        self.handlers[(domain, service)] = handler
        self.schemas[(domain, service)] = schema


class _ConfigEntries:
    def __init__(self) -> None:
        self.entries = {}

    def async_get_entry(self, entry_id: str):
        return self.entries.get(entry_id)


class _Hass:
    def __init__(self) -> None:
        self.services = _Services()
        self.config_entries = _ConfigEntries()


class _Call:
    def __init__(self, data) -> None:
        self.data = data


def _loaded_entry(gateway):
    return SimpleNamespace(
        entry_id="entry-a",
        domain=DOMAIN,
        state=ConfigEntryState.LOADED,
        runtime_data=SimpleNamespace(gateway=gateway),
    )


def test_send_frame_targets_selected_loaded_config_entry() -> None:
    async def scenario() -> None:
        hass = _Hass()
        gateway_a = SimpleNamespace(async_send=AsyncMock())
        gateway_b = SimpleNamespace(async_send=AsyncMock())
        hass.config_entries.entries["entry-a"] = _loaded_entry(gateway_a)
        entry_b = _loaded_entry(gateway_b)
        entry_b.entry_id = "entry-b"
        hass.config_entries.entries["entry-b"] = entry_b
        await async_setup_services(hass)
        handler = hass.services.handlers[(DOMAIN, SERVICE_SEND_FRAME)]

        await handler(
            _Call(
                {
                    ATTR_CONFIG_ENTRY_ID: "entry-b",
                    "frame": "*1*1*21##",
                }
            )
        )

        gateway_a.async_send.assert_not_awaited()
        gateway_b.async_send.assert_awaited_once_with(
            "*1*1*21##", is_status_request=False
        )
        assert hass.services.schemas[(DOMAIN, SERVICE_SEND_FRAME)] is not None

    asyncio.run(scenario())


def test_send_frame_rejects_missing_or_unloaded_entry() -> None:
    async def scenario() -> None:
        hass = _Hass()
        await async_setup_services(hass)
        handler = hass.services.handlers[(DOMAIN, SERVICE_SEND_FRAME)]

        with pytest.raises(ServiceValidationError) as missing:
            await handler(
                _Call(
                    {
                        ATTR_CONFIG_ENTRY_ID: "missing",
                        "frame": "*1*1*21##",
                    }
                )
            )
        assert missing.value.translation_key == "send_frame_entry_not_found"

        gateway = SimpleNamespace(async_send=AsyncMock())
        entry = _loaded_entry(gateway)
        entry.state = ConfigEntryState.NOT_LOADED
        hass.config_entries.entries["entry-a"] = entry
        with pytest.raises(ServiceValidationError) as unloaded:
            await handler(
                _Call(
                    {
                        ATTR_CONFIG_ENTRY_ID: "entry-a",
                        "frame": "*1*1*21##",
                    }
                )
            )
        assert unloaded.value.translation_key == "send_frame_entry_not_loaded"

    asyncio.run(scenario())


def test_send_frame_validates_frame_and_translates_gateway_failure() -> None:
    async def scenario() -> None:
        hass = _Hass()
        gateway = SimpleNamespace(
            async_send=AsyncMock(side_effect=BticinoGatewayError("transport down"))
        )
        hass.config_entries.entries["entry-a"] = _loaded_entry(gateway)
        await async_setup_services(hass)
        handler = hass.services.handlers[(DOMAIN, SERVICE_SEND_FRAME)]

        with pytest.raises(ServiceValidationError) as missing_frame:
            await handler(_Call({ATTR_CONFIG_ENTRY_ID: "entry-a"}))
        assert missing_frame.value.translation_key == "send_frame_missing_frame"

        with pytest.raises(HomeAssistantError) as failed:
            await handler(
                _Call(
                    {
                        ATTR_CONFIG_ENTRY_ID: "entry-a",
                        "frame": "*1*1*21##",
                        "is_status_request": True,
                    }
                )
            )
        assert failed.value.translation_key == "send_frame_failed"
        assert failed.value.translation_placeholders == {"detail": "transport down"}

    asyncio.run(scenario())


def test_arm_alarm_partitions_sends_active_partition_mask() -> None:
    async def scenario() -> None:
        hass = _Hass()
        gateway = SimpleNamespace(async_send=AsyncMock())
        hass.config_entries.entries["entry-a"] = _loaded_entry(gateway)
        await async_setup_services(hass)
        handler = hass.services.handlers[(DOMAIN, SERVICE_ARM_ALARM_PARTITIONS)]

        await handler(
            _Call(
                {
                    ATTR_CONFIG_ENTRY_ID: "entry-a",
                    ATTR_PARTITIONS: [6, 1, 2, 5],
                }
            )
        )

        gateway.async_send.assert_awaited_once_with("*5*8#1256##")

    asyncio.run(scenario())


def test_arm_alarm_partitions_rejects_invalid_partition_list() -> None:
    async def scenario() -> None:
        hass = _Hass()
        gateway = SimpleNamespace(async_send=AsyncMock())
        hass.config_entries.entries["entry-a"] = _loaded_entry(gateway)
        await async_setup_services(hass)
        handler = hass.services.handlers[(DOMAIN, SERVICE_ARM_ALARM_PARTITIONS)]

        with pytest.raises(ServiceValidationError) as invalid:
            await handler(
                _Call(
                    {
                        ATTR_CONFIG_ENTRY_ID: "entry-a",
                        ATTR_PARTITIONS: [9],
                    }
                )
            )
        assert invalid.value.translation_key == "alarm_partitions_invalid"
        gateway.async_send.assert_not_awaited()

    asyncio.run(scenario())
