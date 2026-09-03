"""Structured representation of an OpenWebNet frame."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OpenWebNetFrame:
    """A parsed OpenWebNet event or dimension response."""

    who: str
    what: str | None
    where: str
    raw: str
    dimension: str | None = None
    values: tuple[str, ...] = ()

    @property
    def key(self) -> str:
        """Return the canonical WHO/WHERE endpoint key."""
        return f"{self.who}-{self.where}"

    @property
    def is_dimension(self) -> bool:
        """Return whether this is a dimension response."""
        return self.dimension is not None
