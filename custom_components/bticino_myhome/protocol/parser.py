"""OpenWebNet frame parser."""
from __future__ import annotations

import re

from .frame import OpenWebNetFrame

_STANDARD_RE = re.compile(
    r"^\*(?P<who>[^*#]+)\*(?P<what>[^*#]+)\*(?P<where>[^*#]+)##$"
)
_THERMOREGULATION_CENTRAL_RE = re.compile(
    r"^\*4\*(?P<what>[^*#]+)\*(?P<where>#[^*#]+)##$"
)


def parse_frame(raw_message: str) -> OpenWebNetFrame | None:
    """Parse standard events and dimension responses.

    Command/status requests such as ``*#1*21##`` and dimension writes with a
    ``#DIM`` marker are intentionally not emitted as device events. Parameterized
    standard ``#WHERE`` values are accepted only for WHO=4 central-unit zone
    events; other WHO families remain conservative until their group/address
    semantics are explicitly implemented.
    """
    if raw_message is None:
        return None
    raw = str(raw_message).strip()
    if not raw:
        return None

    standard = _STANDARD_RE.fullmatch(raw)
    if standard is not None:
        return OpenWebNetFrame(
            who=standard.group("who"),
            what=standard.group("what"),
            where=standard.group("where"),
            raw=raw,
        )

    thermoregulation_central = _THERMOREGULATION_CENTRAL_RE.fullmatch(raw)
    if thermoregulation_central is not None:
        return OpenWebNetFrame(
            who="4",
            what=thermoregulation_central.group("what"),
            where=thermoregulation_central.group("where"),
            raw=raw,
        )

    if not raw.startswith("*#") or not raw.endswith("##"):
        return None

    parts = raw[2:-2].split("*")
    if len(parts) < 3:
        return None
    who, where, dimension, *values = parts
    if not who or not where or not dimension or dimension.startswith("#"):
        return None

    return OpenWebNetFrame(
        who=who,
        what=None,
        where=where,
        raw=raw,
        dimension=dimension,
        values=tuple(values),
    )
