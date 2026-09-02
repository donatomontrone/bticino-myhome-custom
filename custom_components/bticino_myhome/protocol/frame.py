"""Structured representation of an OpenWebNet frame."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OpenWebNetFrame:
    """A parsed OpenWebNet event/response frame.

    ``who``, ``what`` and ``where`` remain strings because OpenWebNet addresses
    are not universally numeric and some installations use composite values.
    """

    who: str
    what: str
    where: str
    raw: str

    @property
    def key(self) -> str:
        """Return the canonical WHO/WHERE endpoint key."""
        return f"{self.who}-{self.where}"
