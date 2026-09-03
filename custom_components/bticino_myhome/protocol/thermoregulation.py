"""OpenWebNet WHO=4 thermoregulation helpers.

The constants and builders in this module follow the public BTicino/Legrand
OpenWebNet WHO=4 specification. Real MH201 validation is still required before
removing the experimental status from the platform.
"""
from __future__ import annotations

from .commands import build_command, build_dimension_write

WHO_THERMOREGULATION = "4"

DIM_MEASURED_TEMPERATURE = "0"
DIM_COMPLETE_PROBE_STATUS = "12"
DIM_SETPOINT_TEMPERATURE = "14"
DIM_VALVES_STATUS = "19"

OPERATION_MODE_HEATING = "1"
OPERATION_MODE_CONDITIONING = "2"
OPERATION_MODE_GENERIC = "3"

CLIMATE_PROFILE_HEATING = "heating"
CLIMATE_PROFILE_COOLING = "cooling"
CLIMATE_PROFILE_HEATING_COOLING = "heating_cooling"
CLIMATE_PROFILES = {
    CLIMATE_PROFILE_HEATING,
    CLIMATE_PROFILE_COOLING,
    CLIMATE_PROFILE_HEATING_COOLING,
}

CAPABILITY_HEATING = "heating"
CAPABILITY_COOLING = "cooling"

STATE_CONDITIONING = "conditioning"
STATE_HEATING = "heating"
STATE_ANTIFREEZE = "antifreeze"
STATE_THERMAL_PROTECTION = "thermal_protection"
STATE_GENERIC_PROTECTION = "generic_protection"
STATE_OFF_HEATING = "off_heating"
STATE_OFF_CONDITIONING = "off_conditioning"
STATE_OFF_GENERIC = "off_generic"
STATE_MANUAL_HEATING = "manual_heating"
STATE_MANUAL_CONDITIONING = "manual_conditioning"
STATE_MANUAL_GENERIC = "manual_generic"
STATE_PROGRAMMING_HEATING = "programming_heating"
STATE_PROGRAMMING_CONDITIONING = "programming_conditioning"
STATE_PROGRAMMING_GENERIC = "programming_generic"

THERMOREGULATION_STATE_MAP = {
    "0": STATE_CONDITIONING,
    "1": STATE_HEATING,
    "102": STATE_ANTIFREEZE,
    "202": STATE_THERMAL_PROTECTION,
    "302": STATE_GENERIC_PROTECTION,
    "103": STATE_OFF_HEATING,
    "203": STATE_OFF_CONDITIONING,
    "303": STATE_OFF_GENERIC,
    "110": STATE_MANUAL_HEATING,
    "210": STATE_MANUAL_CONDITIONING,
    "310": STATE_MANUAL_GENERIC,
    "111": STATE_PROGRAMMING_HEATING,
    "211": STATE_PROGRAMMING_CONDITIONING,
    "311": STATE_PROGRAMMING_GENERIC,
}

_HEATING_STATES = {
    STATE_HEATING,
    STATE_ANTIFREEZE,
    STATE_OFF_HEATING,
    STATE_MANUAL_HEATING,
    STATE_PROGRAMMING_HEATING,
}
_COOLING_STATES = {
    STATE_CONDITIONING,
    STATE_THERMAL_PROTECTION,
    STATE_OFF_CONDITIONING,
    STATE_MANUAL_CONDITIONING,
    STATE_PROGRAMMING_CONDITIONING,
}

# WHO=4 DIM=19 documents 1/2 and 6/7/8 as active states. Values 0, 3,
# 4 and 5 are explicitly inactive. Community clarification from the MyOPEN
# team additionally identifies 14/15/16 as OFF fan-coil speed states.
_ACTIVE_OUTPUT_STATES = {1, 2, 6, 7, 8}


def capabilities_for_climate_profile(profile: str) -> tuple[str, ...]:
    """Return explicit heating/cooling capabilities for a configured zone profile."""
    value = str(profile).strip()
    if value == CLIMATE_PROFILE_HEATING:
        return (CAPABILITY_HEATING,)
    if value == CLIMATE_PROFILE_COOLING:
        return (CAPABILITY_COOLING,)
    if value == CLIMATE_PROFILE_HEATING_COOLING:
        return (CAPABILITY_HEATING, CAPABILITY_COOLING)
    raise ValueError(f"Unsupported climate profile: {profile}")


def capabilities_for_thermoregulation_state(state: str | None) -> tuple[str, ...]:
    """Infer thermal direction only when the documented WHAT family proves it."""
    if state in _HEATING_STATES:
        return (CAPABILITY_HEATING,)
    if state in _COOLING_STATES:
        return (CAPABILITY_COOLING,)
    return ()


def central_zone_where(where: str) -> str:
    """Return the WHO=4 WHERE form used for commands through the central unit."""
    value = str(where).strip()
    if not value:
        raise ValueError("Thermoregulation WHERE is required")
    return value if value.startswith("#") else f"#{value}"


def encode_setpoint_temperature(temperature: float) -> str:
    """Encode a WHO=4 writable setpoint using the documented 0.5 °C step."""
    value = float(temperature)
    if not 5.0 <= value <= 40.0:
        raise ValueError(f"Temperature out of range: {value}")
    rounded = int(value * 2 + 0.5) / 2
    return f"{int(rounded * 10):04d}"


def build_zone_mode_command(where: str, what: str) -> str:
    """Build a WHO=4 zone mode command routed through the central unit."""
    return build_command(WHO_THERMOREGULATION, what, central_zone_where(where))


def build_zone_setpoint_command(
    where: str, temperature: float, operation_mode: str
) -> str:
    """Build the documented *#4*WHERE*#14*T*M## zone setpoint command."""
    mode = str(operation_mode)
    if mode not in {
        OPERATION_MODE_HEATING,
        OPERATION_MODE_CONDITIONING,
        OPERATION_MODE_GENERIC,
    }:
        raise ValueError(f"Unsupported thermoregulation operation mode: {mode}")
    return build_dimension_write(
        WHO_THERMOREGULATION,
        central_zone_where(where),
        DIM_SETPOINT_TEMPERATURE,
        encode_setpoint_temperature(temperature),
        mode,
    )


def output_is_active(value: str) -> bool:
    """Return whether a DIM=19 valve/fan-coil value represents active output."""
    try:
        return int(value) in _ACTIVE_OUTPUT_STATES
    except (TypeError, ValueError):
        return False
