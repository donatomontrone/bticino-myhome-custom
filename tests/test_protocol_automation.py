"""Tests for OpenWebNet WHO=2 advanced-shutter protocol helpers."""
from __future__ import annotations

import pytest

from custom_components.bticino_myhome.discovery import BticinoDiscovery
from custom_components.bticino_myhome.protocol import normalize_frame, parse_frame
from custom_components.bticino_myhome.protocol.automation import (
    CAPABILITY_POSITION_CONTROL,
    DEFAULT_GO_TO_LEVEL_PRIORITY,
    SHUTTER_STATUS_DOWN,
    SHUTTER_STATUS_STEP_DOWN,
    SHUTTER_STATUS_STEP_UP,
    SHUTTER_STATUS_STOP,
    SHUTTER_STATUS_UP,
    build_go_to_level,
    decode_shutter_status,
)


def test_decode_documented_shutter_status_payload() -> None:
    status = decode_shutter_status(("11", "45", "001", "0"))

    assert status is not None
    assert status.status == SHUTTER_STATUS_UP
    assert status.position == 45
    assert status.priority == "001"
    assert status.info == 0
    assert status.is_opening is True
    assert status.is_closing is False
    assert status.is_closed is False


@pytest.mark.parametrize(
    ("raw_status", "is_opening", "is_closing"),
    [
        (SHUTTER_STATUS_STOP, False, False),
        (SHUTTER_STATUS_UP, True, False),
        (SHUTTER_STATUS_DOWN, False, True),
        (SHUTTER_STATUS_STEP_UP, True, False),
        (SHUTTER_STATUS_STEP_DOWN, False, True),
    ],
)
def test_decode_documented_motion_states(
    raw_status: int,
    is_opening: bool,
    is_closing: bool,
) -> None:
    status = decode_shutter_status((str(raw_status), "50"))

    assert status is not None
    assert status.is_opening is is_opening
    assert status.is_closing is is_closing


def test_decode_unknown_position_preserves_unknown() -> None:
    status = decode_shutter_status(("10", "255", "001", "0"))

    assert status is not None
    assert status.position is None
    assert status.is_closed is None


def test_decode_closed_and_open_endpoints() -> None:
    closed = decode_shutter_status(("10", "0"))
    opened = decode_shutter_status(("10", "100"))

    assert closed is not None
    assert closed.position == 0
    assert closed.is_closed is True
    assert opened is not None
    assert opened.position == 100
    assert opened.is_closed is False


@pytest.mark.parametrize(
    "values",
    [
        (),
        ("10",),
        ("9", "50"),
        ("invalid", "50"),
        ("10", "invalid"),
        ("10", "101"),
        ("10", "254"),
        ("10", "256"),
    ],
)
def test_decode_rejects_invalid_payloads(values: tuple[str, ...]) -> None:
    assert decode_shutter_status(values) is None


def test_decode_keeps_valid_status_when_optional_info_is_invalid() -> None:
    status = decode_shutter_status(("10", "25", "001", "unknown"))

    assert status is not None
    assert status.position == 25
    assert status.priority == "001"
    assert status.info is None


def test_build_go_to_level_matches_documented_and_ownd_shape() -> None:
    assert DEFAULT_GO_TO_LEVEL_PRIORITY == "001"
    assert build_go_to_level("11", 45) == "*#2*11*#11#001*45##"
    assert build_go_to_level("11", 0) == "*#2*11*#11#001*0##"
    assert build_go_to_level("11", 100) == "*#2*11*#11#001*100##"
    assert build_go_to_level("11", 45, priority="010") == "*#2*11*#11#010*45##"


@pytest.mark.parametrize("position", [-1, 101])
def test_build_go_to_level_rejects_out_of_range_position(position: int) -> None:
    with pytest.raises(ValueError, match="position out of range"):
        build_go_to_level("11", position)


@pytest.mark.parametrize("priority", ["", "01", "0001", "002", "abc"])
def test_build_go_to_level_rejects_invalid_priority(priority: str) -> None:
    with pytest.raises(ValueError, match="Unsupported shutter priority"):
        build_go_to_level("11", 50, priority=priority)


def test_build_go_to_level_requires_where() -> None:
    with pytest.raises(ValueError, match="WHERE is required"):
        build_go_to_level(" ", 50)


def test_documented_dim10_frame_round_trips_to_normalized_event() -> None:
    frame = parse_frame("*#2*11*10*11*45*001*0##")

    assert frame is not None
    event = normalize_frame(frame)
    assert event.who == "2"
    assert event.where == "11"
    assert event.dimension == "10"
    assert event.values == ("11", "45", "001", "0")


def test_valid_dim10_event_marks_discovered_cover_position_capable() -> None:
    device = BticinoDiscovery.parse_event("*#2*11*10*11*45*001*0##")

    assert device is not None
    assert device.device_type == "cover"
    assert CAPABILITY_POSITION_CONTROL in device.capabilities
    assert device.extra["advanced_shutter"] is True


def test_invalid_dim10_event_does_not_mark_position_capable() -> None:
    device = BticinoDiscovery.parse_event("*#2*11*10*9*45*001*0##")

    assert device is not None
    assert CAPABILITY_POSITION_CONTROL not in device.capabilities
    assert "advanced_shutter" not in device.extra


def test_group_dim10_event_is_not_endpoint_discovery_evidence() -> None:
    assert BticinoDiscovery.parse_event("*#2*#1*10*11*45*001*0##") is None
