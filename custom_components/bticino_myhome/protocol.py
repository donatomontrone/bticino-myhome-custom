"""BTicino MyHome protocol utilities."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ParsedFrame:
    """Parsed OpenWebNet frame."""

    who: str
    what: str | None
    where: str | None
    dimension: str | None = None
    value: str | None = None
    is_status: bool = False
    is_dimension: bool = False


def parse_frame(raw: str) -> ParsedFrame | None:
    """Parse an OpenWebNet frame into structured data.
    
    Handles:
    - Simple frames: *WHO*WHAT*WHERE##
    - Composite addresses: *WHO*WHAT*WHERE#bus##
    - Status requests: *WHO*WHERE##
    - Dimension frames: *#WHO*WHERE*DIM*value##
    - Diagnostic frames: *#1001*...## (returned as-is)
    """
    raw = raw.strip()
    if not raw.startswith("*") or not raw.endswith("##"):
        return None

    # Diagnostic frames (pass through)
    if raw.startswith("*#100"):
        return None

    # Dimension frame: *#WHO*WHERE*DIM*value##
    dim_match = re.match(
        r"^\*#(?P<who>[^*]+)\*(?P<where>[^*]+)\*(?P<dim>[^*]+)\*(?P<value>.+)##$",
        raw[1:-2],  # Strip * and ##
    )
    if dim_match:
        return ParsedFrame(
            who=dim_match.group("who"),
            what=None,
            where=dim_match.group("where"),
            dimension=dim_match.group("dim"),
            value=dim_match.group("value"),
            is_dimension=True,
        )

    # Status request/response: *WHO*WHERE## or *#WHO*WHERE##
    status_match = re.match(
        r"^\*#?(?P<who>[^*]+)\*(?P<where>[^*]+)##$",
        raw[1:-2],
    )
    if status_match:
        return ParsedFrame(
            who=status_match.group("who"),
            what=None,
            where=status_match.group("where"),
            is_status=True,
        )

    # Simple frame: *WHO*WHAT*WHERE## (WHERE can include # for composite addresses)
    simple_match = re.match(
        r"^(?P<who>[^*]+)\*(?P<what>[^*]*)\*(?P<where>.+)$",
        raw[1:-2],
    )
    if simple_match:
        return ParsedFrame(
            who=simple_match.group("who"),
            what=simple_match.group("what") or None,
            where=simple_match.group("where"),
        )

    return None


def build_command(who: str, what: str, where: str) -> str:
    """Build a command frame."""
    return f"*{who}*{what}*{where}##"


def build_status_request(who: str, where: str) -> str:
    """Build a status request frame."""
    return f"*{who}*{where}##"


def normalize_frame(raw: str) -> str:
    """Normalize a frame for comparison/logging."""
    return raw.strip()
