"""Tests for WHO=4 dimension and mode frames."""
from __future__ import annotations

from custom_components.bticino_myhome.protocol import normalize_frame, parse_frame


def test_parse_thermo_temperature_dimension() -> None:
    frame = parse_frame("*#4*1*0*0215##")
    assert frame is not None
    assert frame.who == "4"
    assert frame.where == "1"
    assert frame.dimension == "0"
    assert frame.values == ("0215",)
    event = normalize_frame(frame)
    assert event.device_type == "climate"


def test_parse_thermo_setpoint_dimension_with_extra_value() -> None:
    frame = parse_frame("*#4*1*14*0200*3##")
    assert frame is not None
    assert frame.dimension == "14"
    assert frame.values == ("0200", "3")


def test_parse_thermo_mode_event() -> None:
    frame = parse_frame("*4*110*1##")
    assert frame is not None
    event = normalize_frame(frame)
    assert event.state == "heat"


def test_dimension_write_is_not_treated_as_received_state() -> None:
    assert parse_frame("*#4*1*#14*0215##") is None
