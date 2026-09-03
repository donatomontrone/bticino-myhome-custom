"""Tests for BTicino MyHome protocol layer."""
from __future__ import annotations

from custom_components.bticino_myhome.protocol import (
    DIM_THERMO_TEMPERATURE,
    WHO_THERMOREGULATION,
    parse_frame,
)


def test_parse_thermo_temperature_frame() -> None:
    """Test parsing WHO=4 temperature frame."""
    frame = "*#4*1*0*0215##"
    msg = parse_frame(frame)

    assert msg is not None
    assert msg.who == WHO_THERMOREGULATION
    assert msg.where == "1"
    assert msg.dimension == DIM_THERMO_TEMPERATURE
    assert msg.values == ["0215"]


def test_parse_thermo_setpoint_frame() -> None:
    """Test parsing WHO=4 setpoint frame."""
    frame = "*#4*1*14*0200*3##"
    msg = parse_frame(frame)

    assert msg is not None
    assert msg.who == WHO_THERMOREGULATION
    assert msg.where == "1"
    assert msg.dimension == 14
    assert msg.values == ["0200", "3"]


def test_parse_thermo_mode_frame() -> None:
    """Test parsing WHO=4 mode frame."""
    frame = "*4*110*1##"
    msg = parse_frame(frame)

    assert msg is not None
    assert msg.who == WHO_THERMOREGULATION
    assert msg.what == 110
    assert msg.where == "1"


def test_parse_thermo_setpoint_command() -> None:
    """Test parsing WHO=4 setpoint command."""
    frame = "*#4*1*#14*0215##"
    msg = parse_frame(frame)

    assert msg is not None
    assert msg.who == WHO_THERMOREGULATION
    assert msg.where == "1"
    assert msg.dimension == 14
    assert msg.values == ["0215"]
    assert msg.is_dimension_write is True
