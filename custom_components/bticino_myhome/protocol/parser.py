"""OpenWebNet frame parser."""
from __future__ import annotations

import re

from .frame import OpenWebNetFrame

_FRAME_RE = re.compile(
    r"^\*(?P<who>[^*#]+)\*(?P<what>[^*#]*)\*(?P<where>[^#]+)##$"
)


def parse_frame(raw_message: str) -> OpenWebNetFrame | None:
    """Parse a standard OpenWebNet event frame.

    Status-request frames (``*#...``) and malformed messages are intentionally
    rejected because they are commands rather than device events.
    """
    raw = str(raw_message).strip()
    match = _FRAME_RE.fullmatch(raw)
    if match is None:
        return None
    return OpenWebNetFrame(
        who=match.group("who"),
        what=match.group("what"),
        where=match.group("where"),
        raw=raw,
    )
