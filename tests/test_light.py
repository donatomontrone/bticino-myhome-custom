"""Tests for the WHO=1 ON/OFF-only light entity."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, call

from homeassistant.components.light import ColorMode

from custom_components.bticino_myhome.gateway import BticinoGateway
from custom_components.bticino_myhome.light import BticinoLight
from custom_components.bticino_myhome.protocol import normalize_frame, parse_frame


def _light() -> tuple[BticinoLight, BticinoGateway]:
    gateway = BticinoGateway("127.0.0.1", 20000, "pwd")
    gateway.async_send = AsyncMock()
    return BticinoLight(gateway, "1", "21", "Light 21"), gateway


def _event(raw: str):  # type: ignore[no-untyped-def]
    frame = parse_frame(raw)
    assert frame is not None
    return normalize_frame(frame)


def test_light_exposes_onoff_only() -> None:
    light, _ = _light()

    assert light.color_mode == ColorMode.ONOFF
    assert light.supported_color_modes == {ColorMode.ONOFF}
    assert light.brightness is None


def test_turn_on_sends_documented_who1_frame_without_optimistic_state() -> None:
    async def scenario() -> None:
        light, gateway = _light()

        await light.async_turn_on()

        gateway.async_send.assert_awaited_once_with("*1*1*21##")
        assert light.is_on is None

    asyncio.run(scenario())


def test_turn_off_sends_documented_who1_frame_without_optimistic_state() -> None:
    async def scenario() -> None:
        light, gateway = _light()
        light._handle_event(_event("*1*1*21##"))
        assert light.is_on is True

        await light.async_turn_off()

        gateway.async_send.assert_awaited_once_with("*1*0*21##")
        assert light.is_on is True

    asyncio.run(scenario())


def test_initial_hydration_uses_documented_status_request() -> None:
    async def scenario() -> None:
        light, gateway = _light()

        await light._async_request_initial_state()

        assert gateway.async_send.await_args_list == [
            call("*#1*21##", is_status_request=True),
        ]
        assert light.is_on is None

    asyncio.run(scenario())


def test_on_off_events_update_state() -> None:
    light, _ = _light()

    light._handle_event(_event("*1*1*21##"))
    assert light.is_on is True

    light._handle_event(_event("*1*0*21##"))
    assert light.is_on is False


def test_unknown_who1_what_does_not_overwrite_known_state() -> None:
    light, _ = _light()
    light._handle_event(_event("*1*1*21##"))

    light._handle_event(_event("*1*10*21##"))

    assert light.is_on is True


def test_other_endpoint_events_are_ignored() -> None:
    light, _ = _light()

    light._handle_event(_event("*1*1*22##"))

    assert light.is_on is None
