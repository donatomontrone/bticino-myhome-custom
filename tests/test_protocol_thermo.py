"""Tests for WHO=4 dimension, mode and command frames."""
from __future__ import annotations

import pytest

from custom_components.bticino_myhome.protocol import normalize_frame, parse_frame
from custom_components.bticino_myhome.protocol.thermoregulation import (
    CAPABILITY_COOLING,
    CAPABILITY_HEATING,
    CLIMATE_PROFILE_COOLING,
    CLIMATE_PROFILE_HEATING,
    CLIMATE_PROFILE_HEATING_COOLING,
    OPERATION_MODE_CONDITIONING,
    OPERATION_MODE_GENERIC,
    OPERATION_MODE_HEATING,
    STATE_ANTIFREEZE,
    STATE_GENERIC_PROTECTION,
    STATE_MANUAL_HEATING,
    STATE_THERMAL_PROTECTION,
    build_zone_mode_command,
    build_zone_setpoint_command,
    capabilities_for_climate_profile,
    capabilities_for_thermoregulation_state,
    central_zone_where,
    encode_setpoint_temperature,
    output_is_active,
)


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


def test_parse_thermo_mode_events_use_documented_protection_semantics() -> None:
    expected = {
        "102": STATE_ANTIFREEZE,
        "202": STATE_THERMAL_PROTECTION,
        "302": STATE_GENERIC_PROTECTION,
        "110": STATE_MANUAL_HEATING,
    }
    for what, state in expected.items():
        frame = parse_frame(f"*4*{what}*1##")
        assert frame is not None
        assert normalize_frame(frame).state == state


def test_climate_profiles_map_to_explicit_capabilities() -> None:
    assert capabilities_for_climate_profile(CLIMATE_PROFILE_HEATING) == (
        CAPABILITY_HEATING,
    )
    assert capabilities_for_climate_profile(CLIMATE_PROFILE_COOLING) == (
        CAPABILITY_COOLING,
    )
    assert capabilities_for_climate_profile(CLIMATE_PROFILE_HEATING_COOLING) == (
        CAPABILITY_HEATING,
        CAPABILITY_COOLING,
    )
    with pytest.raises(ValueError):
        capabilities_for_climate_profile("unsupported")


def test_documented_mode_families_prove_thermal_direction() -> None:
    assert capabilities_for_thermoregulation_state(STATE_MANUAL_HEATING) == (
        CAPABILITY_HEATING,
    )
    assert capabilities_for_thermoregulation_state(STATE_THERMAL_PROTECTION) == (
        CAPABILITY_COOLING,
    )
    assert capabilities_for_thermoregulation_state(STATE_GENERIC_PROTECTION) == (
        CAPABILITY_HEATING,
        CAPABILITY_COOLING,
    )
    assert capabilities_for_thermoregulation_state(None) == ()


def test_dimension_write_is_not_treated_as_received_state() -> None:
    assert parse_frame("*#4*#1*#14*0215*1##") is None


def test_zone_where_is_routed_through_central_unit() -> None:
    assert central_zone_where("1") == "#1"
    assert central_zone_where("#1") == "#1"
    assert build_zone_mode_command("1", "110") == "*4*110*#1##"


def test_setpoint_builder_encodes_temperature_and_operation_mode() -> None:
    assert (
        build_zone_setpoint_command("10", 21.5, OPERATION_MODE_HEATING)
        == "*#4*#10*#14*0215*1##"
    )
    assert (
        build_zone_setpoint_command("10", 20.0, OPERATION_MODE_CONDITIONING)
        == "*#4*#10*#14*0200*2##"
    )
    assert (
        build_zone_setpoint_command("10", 19.5, OPERATION_MODE_GENERIC)
        == "*#4*#10*#14*0195*3##"
    )


def test_setpoint_encoding_uses_half_degree_steps_and_bounds() -> None:
    assert encode_setpoint_temperature(21.24) == "0210"
    assert encode_setpoint_temperature(21.26) == "0215"
    with pytest.raises(ValueError):
        encode_setpoint_temperature(4.5)
    with pytest.raises(ValueError):
        encode_setpoint_temperature(40.5)


def test_valve_output_active_states_are_not_any_nonzero_value() -> None:
    assert output_is_active("1") is True
    assert output_is_active("8") is True
    assert output_is_active("0") is False
    assert output_is_active("3") is False
    assert output_is_active("14") is False
    assert output_is_active("invalid") is False
