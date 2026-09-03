"""Tests for the raw OpenWebNet send_frame service."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from homeassistant.exceptions import HomeAssistantError
import pytest

from custom_components.bticino_myhome.const import DOMAIN
from custom_components.bticino_myhome.services import SERVICE_SEND_FRAME, async_setup_services


class _Services:
    def __init__(self) -> None:
        self.handlers = {}

    def has_service(self, domain: str, service: str) -> bool:
        return (domain, service) in self.handlers

    def async_register(self, domain: str, service: str, handler) -> None:
        self.handlers[(domain, service)] = handler

    def async_remove(self, domain: str, service: str) -> None:
        self.handlers.pop((domain, service), None)


class _Hass:
    def __init__(self) -> None:
        self.data = {DOMAIN: {}}
        self.services = _Services()


class _Call:
    def __init__(self, data) -> None:
        self.data = data


def test_send_frame_service_uses_loaded_runtime_gateway() -> None:
    async def scenario() -> None:
        hass = _Hass()
        gateway = SimpleNamespace(async_send=AsyncMock())
        hass.data[DOMAIN]["entry"] = SimpleNamespace(gateway=gateway)
        await async_setup_services(hass)
        handler = hass.services.handlers[(DOMAIN, SERVICE_SEND_FRAME)]
        await handler(_Call({"frame": "*1*1*21##"}))
        gateway.async_send.assert_awaited_once_with(
            "*1*1*21##", is_status_request=False
        )

    asyncio.run(scenario())


def test_send_frame_requires_frame_and_loaded_gateway() -> None:
    async def scenario() -> None:
        hass = _Hass()
        await async_setup_services(hass)
        handler = hass.services.handlers[(DOMAIN, SERVICE_SEND_FRAME)]
        with pytest.raises(HomeAssistantError, match="Frame is required"):
            await handler(_Call({}))
        with pytest.raises(HomeAssistantError, match="No gateway configured"):
            await handler(_Call({"frame": "*1*1*21##"}))

    asyncio.run(scenario())
