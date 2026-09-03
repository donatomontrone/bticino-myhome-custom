"""OpenWebNet WHO=2 automation and advanced-shutter helpers.

The constants and frame shapes in this module follow the public BTicino/Legrand
OpenWebNet WHO=2 specification. The default GoToLevel priority is cross-checked
against the established OWNd implementation. Physical MH201 validation remains
pending.
"""
from __future__ import annotations

from dataclasses import dataclass

WHO_AUTOMATION = "2"

DIM_SHUTTER_STATUS = "10"
DIM_GO_TO_LEVEL = "11"

CAPABILITY_POSITION_CONTROL = "position_control"

SHUTTER_STATUS_STOP = 10
SHUTTER_STATUS_UP = 11
SHUTTER_STATUS_DOWN = 12
SHUTTER_STATUS_STEP_UP = 13
SHUTTER_STATUS_STEP_DOWN = 14
SHUTTER_STATUS_VALUES = {
    SHUTTER_STATUS_STOP,
    SHUTTER_STATUS_UP,
    SHUTTER_STATUS_DOWN,
    SHUTTER_STATUS_STEP_UP,
    SHUTTER_STATUS_STEP_DOWN,
}

SHUTTER_LEVEL_UNKNOWN = 255

# OWNd's set_shutter_level() uses #001 for the mandatory priority field in the
# documented WHO=2 DIM=11 GoToLevel frame. Keep this compatibility value
# explicit until real MH201 captures let us validate installation-specific
# priority behavior.
DEFAULT_GO_TO_LEVEL_PRIORITY = "001"


@dataclass(frozen=True, slots=True)
class AdvancedShutterStatus:
    """Typed state decoded from a documented WHO=2 DIM=10 payload."""

    status: int
    position: int | None
    priority: str | None = None
    info: int | None = None

    @property
    def is_opening(self) -> bool:
        return self.status in {SHUTTER_STATUS_UP, SHUTTER_STATUS_STEP_UP}

    @property
    def is_closing(self) -> bool:
        return self.status in {SHUTTER_STATUS_DOWN, SHUTTER_STATUS_STEP_DOWN}

    @property
    def is_closed(self) -> bool | None:
        if self.position is None:
            return None
        return self.position == 0


def decode_shutter_status(values: tuple[str, ...]) -> AdvancedShutterStatus | None:
    """Decode DIM=10 status, preserving 255 as unknown position."""
    if len(values) < 2:
        return None
    try:
        status = int(values[0])
        raw_level = int(values[1])
    except (TypeError, ValueError):
        return None
    if status not in SHUTTER_STATUS_VALUES:
        return None
    if raw_level == SHUTTER_LEVEL_UNKNOWN:
        position = None
    elif 0 <= raw_level <= 100:
        position = raw_level
    else:
        return None

    priority = values[2] if len(values) > 2 else None
    info: int | None = None
    if len(values) > 3:
        try:
            info = int(values[3])
        except (TypeError, ValueError):
            info = None

    return AdvancedShutterStatus(
        status=status,
        position=position,
        priority=priority,
        info=info,
    )


def build_go_to_level(
    where: str,
    position: int,
    *,
    priority: str = DEFAULT_GO_TO_LEVEL_PRIORITY,
) -> str:
    """Build the documented WHO=2 DIM=11 GoToLevel command."""
    address = str(where).strip()
    if not address:
        raise ValueError("Automation WHERE is required")
    level = int(position)
    if not 0 <= level <= 100:
        raise ValueError(f"Shutter position out of range: {position}")
    priority_value = str(priority).strip()
    if len(priority_value) != 3 or any(bit not in "01" for bit in priority_value):
        raise ValueError(f"Unsupported shutter priority: {priority}")
    return f"*#2*{address}*#11#{priority_value}*{level}##"
