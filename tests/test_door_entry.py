"""Tests for the reference-backed WHO=6 door-entry release surface."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

from custom_components.bticino_myhome.button import BticinoDoorLockRelease
from custom_components.bticino_myhome.gateway import BticinoGateway
from custom_components.bticino_myhome.protocol.door_entry import door_lock_release


def test_door_release_builder_uses_established_who6_frame() -> None:
    assert door_lock_release("4000") == "*6*10*4000##"


def test_door_release_requires_an_address() -> None:
    try:
        door_lock_release("")
    except ValueError:
        pass
    else:
        raise AssertionError("empty door-entry WHERE must be rejected")


def test_door_release_button_sends_who6_frame() -> None:
    async def scenario() -> None:
        gateway = BticinoGateway("127.0.0.1", 20000, "pwd")
        gateway.async_send = AsyncMock()
        button = BticinoDoorLockRelease(gateway, "6", "4000", "Cancello")

        await button.async_press()

        gateway.async_send.assert_awaited_once_with("*6*10*4000##")

    asyncio.run(scenario())
