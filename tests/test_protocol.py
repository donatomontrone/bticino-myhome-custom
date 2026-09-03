"""Tests for the canonical OpenWebNet protocol layer."""
from __future__ import annotations

from custom_components.bticino_myhome.protocol import (
    build_dimension_request,
    build_dimension_write,
    build_status_request,
    cover_close,
    light_on,
    normalize_frame,
    parse_frame,
)


def test_command_builders() -> None:
    assert light_on("21") == "*1*1*21##"
    assert cover_close("11") == "*2*2*11##"
    assert build_status_request("1", "21") == "*#1*21##"
    assert build_dimension_request("4", "1", "14") == "*#4*1*14##"
    assert build_dimension_write("4", "1", "14", "0215") == "*#4*1*#14*0215##"


def test_standard_event_is_parsed_and_normalized() -> None:
    frame = parse_frame("  *1*1*21##  ")
    assert frame is not None
    assert (frame.who, frame.what, frame.where) == ("1", "1", "21")
    event = normalize_frame(frame)
    assert event.device_type == "light"
    assert event.state == "on"


def test_thermoregulation_central_where_is_parseable() -> None:
    frame = parse_frame("*4*110*#1##")
    assert frame is not None
    assert (frame.who, frame.what, frame.where) == ("4", "110", "#1")


def test_parameterized_standard_where_is_not_generic_endpoint_evidence() -> None:
    assert parse_frame("*1*1*#1##") is None
    assert parse_frame("*2*1*#11##") is None


def test_status_requests_and_malformed_frames_are_not_events() -> None:
    assert parse_frame("*#1*21##") is None
    assert parse_frame("*#4*1*#14*0215##") is None
    assert parse_frame("*1*1##") is None
    assert parse_frame("garbage") is None


def test_unknown_standard_who_remains_parseable() -> None:
    frame = parse_frame("*99*1*7##")
    assert frame is not None
    event = normalize_frame(frame)
    assert event.device_type is None
    assert event.state is None
