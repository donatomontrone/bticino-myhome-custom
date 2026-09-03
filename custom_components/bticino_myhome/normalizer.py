"""Normalizer layer for BTicino MyHome integration."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from .protocol import (
    DIM_THERMO_LOCAL_OFFSET,
    DIM_THERMO_PROBE_STATUS,
    DIM_THERMO_SETPOINT,
    DIM_THERMO_TEMPERATURE,
    DIM_THERMO_VALVES,
    OpenWebNetMessage,
    WHO_THERMOREGULATION,
    WHAT_THERMO_ANTIFREEZE,
    WHAT_THERMO_COOLING,
    WHAT_THERMO_HEATING,
    WHAT_THERMO_MANUAL_COOLING,
    WHAT_THERMO_MANUAL_GENERIC,
    WHAT_THERMO_MANUAL_HEATING,
    WHAT_THERMO_OFF_COOLING,
    WHAT_THERMO_OFF_GENERIC,
    WHAT_THERMO_OFF_HEATING,
    WHAT_THERMO_PROGRAM_COOLING,
    WHAT_THERMO_PROGRAM_GENERIC,
    WHAT_THERMO_PROGRAM_HEATING,
    WHAT_THERMO_PROTECTION,
    WHAT_THERMO_THERMAL_PROTECTION,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class NormalizedEvent:
    """Normalized event from OpenWebNet frame."""

    device_type: str
    device_id: str
    event_type: str
    data: dict[str, Any]

    @classmethod
    def from_manual(
        cls,
        device_type: str,
        device_id: str,
        event_type: str,
        data: dict[str, Any],
    ) -> NormalizedEvent:
        """Create a normalized event from manual frame."""
        return cls(
            device_type=device_type,
            device_id=device_id,
            event_type=event_type,
            data=data,
        )


def normalize_event(msg: OpenWebNetMessage) -> NormalizedEvent | None:
    """Normalize an OpenWebNet message into a standard event."""
    if msg.who == WHO_THERMOREGULATION:
        return _normalize_thermo(msg)

    # Add other WHO handlers here
    return None


def _normalize_thermo(msg: OpenWebNetMessage) -> NormalizedEvent | None:
    """Normalize WHO=4 (thermoregulation) messages."""
    if msg.where is None:
        return None

    # Handle dimension messages
    if msg.dimension is not None:
        return _normalize_thermo_dimension(msg)

    # Handle status messages (temperature, mode, etc.)
    if msg.what is not None:
        return _normalize_thermo_status(msg)

    return None


def _normalize_thermo_dimension(msg: OpenWebNetMessage) -> NormalizedEvent | None:
    """Normalize WHO=4 dimension messages."""
    where = msg.where
    dimension = msg.dimension
    values = msg.values or []

    # Temperature measurement (DIM=0)
    if dimension == DIM_THERMO_TEMPERATURE and len(values) >= 1:
        temp_raw = values[0]
        if len(temp_raw) == 4:
            # Convert 4-digit temp to float (e.g., "0215" -> 21.5)
            temp_value = int(temp_raw) / 10.0
            return NormalizedEvent(
                device_type="climate",
                device_id=f"thermo_{where}",
                event_type="temperature",
                data={"temperature": temp_value, "where": where},
            )

    # Setpoint temperature (DIM=14)
    if dimension == DIM_THERMO_SETPOINT and len(values) >= 1:
        temp_raw = values[0]
        if len(temp_raw) == 4:
            temp_value = int(temp_raw) / 10.0
            return NormalizedEvent(
                device_type="climate",
                device_id=f"thermo_{where}",
                event_type="setpoint",
                data={"setpoint": temp_value, "where": where},
            )

    # Local offset (DIM=13)
    if dimension == DIM_THERMO_LOCAL_OFFSET and len(values) >= 1:
        offset_raw = values[0]
        offset_value = _parse_offset(offset_raw)
        return NormalizedEvent(
            device_type="climate",
            device_id=f"thermo_{where}",
            event_type="offset",
            data={"offset": offset_value, "where": where},
        )

    # Probe status with mode (DIM=12)
    if dimension == DIM_THERMO_PROBE_STATUS and len(values) >= 2:
        temp_raw = values[0]
        mode_raw = values[1]
        if len(temp_raw) == 4:
            temp_value = int(temp_raw) / 10.0
            mode_value = _parse_mode(int(mode_raw))
            return NormalizedEvent(
                device_type="climate",
                device_id=f"thermo_{where}",
                event_type="probe_status",
                data={
                    "temperature": temp_value,
                    "mode": mode_value,
                    "where": where,
                },
            )

    # Valves status (DIM=19)
    if dimension == DIM_THERMO_VALVES and len(values) >= 2:
        cv = int(values[0])
        hv = int(values[1])
        return NormalizedEvent(
            device_type="climate",
            device_id=f"thermo_{where}",
            event_type="valves",
            data={"cooling_valve": cv, "heating_valve": hv, "where": where},
        )

    return None


def _normalize_thermo_status(msg: OpenWebNetMessage) -> NormalizedEvent | None:
    """Normalize WHO=4 status messages (mode changes)."""
    where = msg.where
    what = msg.what

    if what is None:
        return None

    mode_value = _parse_mode(what)
    return NormalizedEvent(
        device_type="climate",
        device_id=f"thermo_{where}",
        event_type="mode",
        data={"mode": mode_value, "where": where},
    )


def _parse_offset(offset_str: str) -> float:
    """Parse local offset value."""
    offset_map = {
        "00": 0.0,
        "01": 1.0,
        "11": -1.0,
        "02": 2.0,
        "12": -2.0,
        "03": 3.0,
        "13": -3.0,
        "4": None,  # Local OFF
        "5": None,  # Local protection
    }
    return offset_map.get(offset_str, 0.0)


def _parse_mode(what: int) -> str:
    """Parse WHAT value to HVAC mode."""
    mode_map = {
        WHAT_THERMO_COOLING: "cool",
        WHAT_THERMO_HEATING: "heat",
        WHAT_THERMO_ANTIFREEZE: "eco",
        WHAT_THERMO_THERMAL_PROTECTION: "eco",
        WHAT_THERMO_PROTECTION: "eco",
        WHAT_THERMO_OFF_HEATING: "off",
        WHAT_THERMO_OFF_COOLING: "off",
        WHAT_THERMO_OFF_GENERIC: "off",
        WHAT_THERMO_MANUAL_HEATING: "heat",
        WHAT_THERMO_MANUAL_COOLING: "cool",
        WHAT_THERMO_MANUAL_GENERIC: "auto",
        WHAT_THERMO_PROGRAM_HEATING: "auto",
        WHAT_THERMO_PROGRAM_COOLING: "auto",
        WHAT_THERMO_PROGRAM_GENERIC: "auto",
    }
    return mode_map.get(what, "auto")
