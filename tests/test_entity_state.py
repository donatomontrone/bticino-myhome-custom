"""Tests for deterministic entity state hydration."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

from custom_components.bticino_myhome.cover import BticinoCover
from custom_components.bticino_myhome.gateway import BticinoGateway
from custom_components.bticino_myhome.light import BticinoLight
from custom_components.bticino_myhome.switch import BticinoLoadSwitch


def _gateway() -> BticinoGateway:
    gateway = BticinoGateway("127.0.0.1", 20000, "pwd")
    gateway.async_send = AsyncMock()
    return gateway


def test_initial_state_requests_for_capture_safe_core_entities() -> None:
    async def scenario() -> None:
        cases = [
            (BticinoLight, "1", "21", "*#1*21##"),
            (BticinoCover, "2", "22", "*#2*22##"),
            (BticinoLoadSwitch, "3", "23", "*#3*23##"),
        ]
        for entity_type, who, where, expected in cases:
            gateway = _gateway()
            entity = entity_type(gateway, who, where, "Test")
            assert entity._request_initial_state_on_add is True
            await entity._async_request_initial_state()
            gateway.async_send.assert_awaited_once_with(
                expected,
                is_status_request=True,
            )

    asyncio.run(scenario())
