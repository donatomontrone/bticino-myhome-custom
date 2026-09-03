"""Tests for the WHO=2 cover entity."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, call

import pytest
from homeassistant.components.cover import CoverEntityFeature
from homeassistant.exceptions import ServiceValidationError

from custom_components.bticino_myhome.cover import BticinoCover
from custom_components.bticino_myhome.gateway import BticinoGateway, BticinoGatewayError
from custom_components.bticino_myhome.protocol import normalize_frame, parse_frame
from custom_components.bticino_myhome.protocol.automation import CAPABILITY_POSITION_CONTROL


def _cover(
    capabilities: tuple[str, ...] = (),
) -> tuple[BticinoCover, BticinoGateway]:
    gateway = BticinoGateway("127.0.0.1", 20000, "pwd")
    gateway.async_send = AsyncMock()
    return (
        BticinoCover(
            gateway,
            "2",
            "11",
            "Shutter 11",
            capabilities=capabilities,
        ),
        gateway,
    )


def _event(raw: str):  # type: ignore[no-untyped-def]
    frame = parse_frame(raw)
    assert frame is not None
    return normalize_frame(frame)


def test_basic_cover_does_not_expose_position_control() -> None:
    cover, _ = _cover()

    assert cover.supported_features & CoverEntityFeature.OPEN
    assert cover.supported_features & CoverEntityFeature.CLOSE
    assert cover.supported_features & CoverEntityFeature.STOP
    assert not cover.supported_features & CoverEntityFeature.SET_POSITION
    assert cover.current_cover_position is None


def test_advanced_cover_exposes_position_control() -> None:
    cover, _ = _cover((CAPABILITY_POSITION_CONTROL,))

    assert cover.supported_features & CoverEntityFeature.SET_POSITION
    assert cover.current_cover_position is None


def test_basic_cover_initial_hydration_uses_only_generic_status() -> None:
    async def scenario() -> None:
        cover, gateway = _cover()

        await cover._async_request_initial_state()

        assert gateway.async_send.await_args_list == [
            call("*#2*11##", is_status_request=True),
        ]

    asyncio.run(scenario())


def test_advanced_cover_initial_hydration_requests_dim10() -> None:
    async def scenario() -> None:
        cover, gateway = _cover((CAPABILITY_POSITION_CONTROL,))

        await cover._async_request_initial_state()

        assert gateway.async_send.await_args_list == [
            call("*#2*11##", is_status_request=True),
            call("*#2*11*10##", is_status_request=True),
        ]

    asyncio.run(scenario())


def test_missing_dim10_response_does_not_fail_advanced_hydration() -> None:
    async def scenario() -> None:
        cover, gateway = _cover((CAPABILITY_POSITION_CONTROL,))
        gateway.async_send.side_effect = [None, BticinoGatewayError("DIM unavailable")]

        await cover._async_request_initial_state()

        assert gateway.async_send.await_count == 2
        assert cover.current_cover_position is None

    asyncio.run(scenario())


def test_set_position_sends_go_to_level_without_optimistic_state() -> None:
    async def scenario() -> None:
        cover, gateway = _cover((CAPABILITY_POSITION_CONTROL,))

        await cover.async_set_cover_position(position=40)

        gateway.async_send.assert_awaited_once_with("*#2*11*#11#001*40##")
        assert cover.current_cover_position is None
        assert cover.is_opening is None
        assert cover.is_closing is None

    asyncio.run(scenario())


def test_basic_cover_rejects_position_action_with_translated_error() -> None:
    async def scenario() -> None:
        cover, gateway = _cover()

        with pytest.raises(ServiceValidationError) as error:
            await cover.async_set_cover_position(position=40)

        assert error.value.translation_key == "cover_position_not_supported"
        gateway.async_send.assert_not_awaited()

    asyncio.run(scenario())


def test_out_of_range_position_uses_translated_error() -> None:
    async def scenario() -> None:
        cover, gateway = _cover((CAPABILITY_POSITION_CONTROL,))

        with pytest.raises(ServiceValidationError) as error:
            await cover.async_set_cover_position(position=101)

        assert error.value.translation_key == "cover_position_out_of_range"
        assert error.value.translation_placeholders == {"position": "101"}
        gateway.async_send.assert_not_awaited()

    asyncio.run(scenario())


def test_dim10_opening_event_updates_position_and_motion() -> None:
    cover, _ = _cover((CAPABILITY_POSITION_CONTROL,))

    cover._handle_event(_event("*#2*11*10*11*45*001*0##"))

    assert cover.current_cover_position == 45
    assert cover.is_opening is True
    assert cover.is_closing is False
    assert cover.is_closed is False


def test_dim10_closing_and_step_states_update_motion() -> None:
    cover, _ = _cover((CAPABILITY_POSITION_CONTROL,))

    cover._handle_event(_event("*#2*11*10*12*60*001*0##"))
    assert cover.current_cover_position == 60
    assert cover.is_opening is False
    assert cover.is_closing is True

    cover._handle_event(_event("*#2*11*10*13*55*001*0##"))
    assert cover.is_opening is True
    assert cover.is_closing is False

    cover._handle_event(_event("*#2*11*10*14*50*001*0##"))
    assert cover.is_opening is False
    assert cover.is_closing is True


def test_dim10_stopped_closed_event_sets_closed_state() -> None:
    cover, _ = _cover((CAPABILITY_POSITION_CONTROL,))

    cover._handle_event(_event("*#2*11*10*10*0*001*0##"))

    assert cover.current_cover_position == 0
    assert cover.is_opening is False
    assert cover.is_closing is False
    assert cover.is_closed is True


def test_dim10_unknown_position_remains_unknown() -> None:
    cover, _ = _cover((CAPABILITY_POSITION_CONTROL,))

    cover._handle_event(_event("*#2*11*10*10*255*001*0##"))

    assert cover.current_cover_position is None
    assert cover.is_opening is False
    assert cover.is_closing is False
    assert cover.is_closed is None


def test_invalid_dim10_event_does_not_overwrite_known_position() -> None:
    cover, _ = _cover((CAPABILITY_POSITION_CONTROL,))
    cover._handle_event(_event("*#2*11*10*10*25*001*0##"))

    cover._handle_event(_event("*#2*11*10*9*90*001*0##"))

    assert cover.current_cover_position == 25
    assert cover.is_opening is False
    assert cover.is_closing is False


def test_standard_who2_events_preserve_basic_motion_support() -> None:
    cover, _ = _cover()

    cover._handle_event(_event("*2*1*11##"))
    assert cover.is_opening is True
    assert cover.is_closing is False

    cover._handle_event(_event("*2*2*11##"))
    assert cover.is_opening is False
    assert cover.is_closing is True

    cover._handle_event(_event("*2*0*11##"))
    assert cover.is_opening is False
    assert cover.is_closing is False


def test_events_for_other_endpoints_are_ignored() -> None:
    cover, _ = _cover((CAPABILITY_POSITION_CONTROL,))

    cover._handle_event(_event("*#2*12*10*11*80*001*0##"))

    assert cover.current_cover_position is None
    assert cover.is_opening is None
    assert cover.is_closing is None
