"""Reference-backed OpenWebNet door-entry helpers.

BTicino's public local-interoperability catalogue documents WHO=7 as the
multimedia/camera family. Door-entry control frames are historically exposed as
WHO=6 by VDE-capable MyHOME gateways but are not part of the public WHO PDFs.
The release command below follows long-standing openHAB/community usage and
must therefore remain hardware-validation pending on MH201/HomeTouch.
"""
from __future__ import annotations

WHO_DOOR_ENTRY = "6"
WHAT_DOOR_RELEASE = "10"


def door_lock_release(where: str) -> str:
    """Build the established WHO=6 door/gate release frame."""
    address = str(where).strip()
    if not address:
        raise ValueError("A door-entry WHERE address is required")
    return f"*{WHO_DOOR_ENTRY}*{WHAT_DOOR_RELEASE}*{address}##"
