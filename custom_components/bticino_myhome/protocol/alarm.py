"""OpenWebNet WHO=5 burglar-alarm semantics.

The event/status catalogue and status requests are defined by the public Legrand
WHO=5 specification. Direct arm/disarm and active-zone-mask builders use the
legacy BTicino burglar-alarm OpenWebNet command syntax documented for older
central units. Their behavior on a 4200C through an MH201 remains hardware
validation pending.
"""
from __future__ import annotations

from collections.abc import Iterable

WHO_ALARM = "5"

WHAT_MAINTENANCE = "0"
WHAT_SYSTEM_ACTIVE = "1"
WHAT_SYSTEM_INACTIVE = "2"
WHAT_DELAY_END = "3"
WHAT_BATTERY_FAULT = "4"
WHAT_BATTERY_OK = "5"
WHAT_NETWORK_FAULT = "6"
WHAT_NETWORK_OK = "7"
WHAT_SYSTEM_ENGAGED = "8"
WHAT_SYSTEM_DISENGAGED = "9"
WHAT_BATTERY_UNLOADED = "10"
WHAT_ZONE_ENGAGED = "11"
WHAT_TECHNICAL_ALARM = "12"
WHAT_TECHNICAL_ALARM_RESET = "13"
WHAT_NO_RECEPTION = "14"
WHAT_INTRUSION_ALARM = "15"
WHAT_TAMPERING_ALARM = "16"
WHAT_ANTI_PANIC_ALARM = "17"
WHAT_ZONE_DISENGAGED = "18"
WHAT_START_PROGRAMMING = "26"
WHAT_STOP_PROGRAMMING = "27"
WHAT_SILENT_ALARM = "31"

ALARM_TRIGGER_WHATS = frozenset(
    {
        WHAT_TECHNICAL_ALARM,
        WHAT_INTRUSION_ALARM,
        WHAT_TAMPERING_ALARM,
        WHAT_ANTI_PANIC_ALARM,
        WHAT_SILENT_ALARM,
    }
)

# The documented legacy OpenWebNet partialization mask is limited to zones 1..8.
MAX_LEGACY_PARTITIONS = 8


def alarm_system_status_request() -> str:
    """Request the complete burglar-alarm system snapshot."""
    return "*#5*0##"


def alarm_partition_status_request(partition: int) -> str:
    """Request active/partialized state for one documented central zone."""
    number = _validate_partition(partition)
    return f"*#5*#{number}##"


def alarm_arm_all() -> str:
    """Build the documented legacy WHO=5 full-engage command."""
    return "*5*8##"


def alarm_disarm_all() -> str:
    """Build the documented legacy WHO=5 disengage command."""
    return "*5*9##"


def alarm_arm_partitions(partitions: Iterable[int]) -> str:
    """Engage the legacy system with exactly the listed zones active.

    BTicino's documented legacy syntax treats the digits after ``#`` as the
    zones that remain active; all other zones in the 1..8 set are partialized.
    """
    active = _normalize_partitions(partitions)
    return f"*5*8#{''.join(str(item) for item in active)}##"


def alarm_partition_activate(partition: int) -> str:
    """Make one documented legacy zone active."""
    number = _validate_partition(partition)
    return f"*5*11*#{number}##"


def alarm_partition_partialize(partition: int) -> str:
    """Partialize one documented legacy zone."""
    number = _validate_partition(partition)
    return f"*5*18*#{number}##"


def partition_from_where(where: str) -> int | None:
    """Return a legacy central-zone number from a WHO=5 #WHERE."""
    text = str(where).strip()
    if not text.startswith("#"):
        return None
    try:
        number = int(text[1:])
    except ValueError:
        return None
    return number if 1 <= number <= MAX_LEGACY_PARTITIONS else None


def _normalize_partitions(partitions: Iterable[int]) -> tuple[int, ...]:
    normalized = tuple(sorted({_validate_partition(item) for item in partitions}))
    if not normalized:
        raise ValueError("At least one active alarm partition is required")
    return normalized


def _validate_partition(partition: int) -> int:
    try:
        number = int(partition)
    except (TypeError, ValueError) as err:
        raise ValueError(f"Invalid alarm partition: {partition!r}") from err
    if not 1 <= number <= MAX_LEGACY_PARTITIONS:
        raise ValueError(
            f"Alarm partition {number} is outside the documented 1-{MAX_LEGACY_PARTITIONS} range"
        )
    return number
