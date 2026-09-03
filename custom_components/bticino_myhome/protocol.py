"""Protocol layer for BTicino MyHome integration."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Final

_LOGGER = logging.getLogger(__name__)


@dataclass
class OpenWebNetMessage:
    """OpenWebNet message representation."""

    who: int
    what: int | None = None
    where: str | None = None
    dimension: int | None = None
    values: list[str] | None = None
    is_status_request: bool = False
    is_dimension_request: bool = False
    is_dimension_write: bool = False

    def __str__(self) -> str:
        """Return string representation."""
        parts = [str(self.who)]
        if self.what is not None:
            parts.append(str(self.what))
        if self.where is not None:
            parts.append(str(self.where))
        if self.dimension is not None:
            parts.append(str(self.dimension))
        if self.values:
            parts.extend(self.values)
        return "*" + "*".join(parts) + "##"


def parse_frame(frame: str) -> OpenWebNetMessage | None:
    """Parse an OpenWebNet frame into a message object."""
    if not frame.startswith("*") or not frame.endswith("##"):
        return None

    # Remove start/end markers
    content = frame[1:-2]
    tags = content.split("*")

    if len(tags) < 1:
        return None

    # Check for status request (*#WHO*WHERE##)
    if tags[0] == "#":
        # Status request: *#WHO*WHERE##
        if len(tags) < 2:
            return None
        try:
            who = int(tags[1])
        except ValueError:
            return None

        where = tags[2] if len(tags) > 2 else None
        dimension = None
        values = None
        is_status_request = True
        is_dimension_request = False
        is_dimension_write = False
        what = None

        # Check for dimension request (*#WHO*WHERE*DIM##)
        if len(tags) > 3 and tags[3].isdigit():
            is_dimension_request = True
            dimension = int(tags[3])
            values = tags[4:] if len(tags) > 4 else None

        return OpenWebNetMessage(
            who=who,
            what=what,
            where=where,
            dimension=dimension,
            values=values,
            is_status_request=is_status_request,
            is_dimension_request=is_dimension_request,
            is_dimension_write=is_dimension_write,
        )

    # Check for dimension write (*#WHO*WHERE*#DIM*VAL##)
    if tags[0].startswith("#") and len(tags) > 1 and tags[1].startswith("#"):
        try:
            who = int(tags[0][1:])
            dimension = int(tags[1][1:])
        except ValueError:
            return None

        where = tags[2] if len(tags) > 2 else None
        values = tags[3:] if len(tags) > 3 else None

        return OpenWebNetMessage(
            who=who,
            what=None,
            where=where,
            dimension=dimension,
            values=values,
            is_status_request=False,
            is_dimension_request=False,
            is_dimension_write=True,
        )

    # Standard message (*WHO*WHAT*WHERE##)
    try:
        who = int(tags[0])
    except ValueError:
        return None

    what = None
    where = None
    dimension = None
    values = None
    is_status_request = False
    is_dimension_request = False
    is_dimension_write = False

    if len(tags) > 1:
        # Check if second tag is WHAT or dimension marker
        if tags[1].startswith("#"):
            # Dimension request/write
            is_dimension_request = True
            try:
                dimension = int(tags[1][1:])
            except ValueError:
                return None
            where = tags[2] if len(tags) > 2 else None
            values = tags[3:] if len(tags) > 3 else None
        else:
            # Standard WHAT
            try:
                what = int(tags[1])
            except ValueError:
                return None
            where = tags[2] if len(tags) > 2 else None

    return OpenWebNetMessage(
        who=who,
        what=what,
        where=where,
        dimension=dimension,
        values=values,
        is_status_request=is_status_request,
        is_dimension_request=is_dimension_request,
        is_dimension_write=is_dimension_write,
    )


# WHO constants
WHO_SCENARIO: Final = 0
WHO_LIGHTING: Final = 1
WHO_AUTOMATION: Final = 2
WHO_THERMOREGULATION: Final = 4
WHO_ALARM: Final = 5
WHO_VIDEO_DOOR: Final = 7
WHO_GATEWAY: Final = 13
WHO_CEN: Final = 15
WHO_ENERGY: Final = 18


# WHO=4 DIMENSION constants
DIM_THERMO_TEMPERATURE: Final = 0
DIM_THERMO_FAN_SPEED: Final = 11
DIM_THERMO_PROBE_STATUS: Final = 12
DIM_THERMO_LOCAL_OFFSET: Final = 13
DIM_THERMO_SETPOINT: Final = 14
DIM_THERMO_VALVES: Final = 19
DIM_THERMO_ACTUATOR: Final = 20
DIM_THERMO_SPLIT: Final = 22
DIM_THERMO_HOLIDAY_END: Final = 30


# WHO=4 WHAT constants (operation modes)
WHAT_THERMO_COOLING: Final = 0
WHAT_THERMO_HEATING: Final = 1
WHAT_THERMO_ANTIFREEZE: Final = 102
WHAT_THERMO_THERMAL_PROTECTION: Final = 202
WHAT_THERMO_PROTECTION: Final = 302
WHAT_THERMO_OFF_HEATING: Final = 103
WHAT_THERMO_OFF_COOLING: Final = 203
WHAT_THERMO_OFF_GENERIC: Final = 303
WHAT_THERMO_MANUAL_HEATING: Final = 110
WHAT_THERMO_MANUAL_COOLING: Final = 210
WHAT_THERMO_MANUAL_GENERIC: Final = 310
WHAT_THERMO_PROGRAM_HEATING: Final = 111
WHAT_THERMO_PROGRAM_COOLING: Final = 211
WHAT_THERMO_PROGRAM_GENERIC: Final = 311
