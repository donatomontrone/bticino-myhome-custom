"""Translate OpenWebNet frames into integration-level semantic events."""
from __future__ import annotations

from dataclasses import dataclass

from .frame import OpenWebNetFrame


@dataclass(frozen=True, slots=True)
class NormalizedEvent:
    """Semantic event consumed by Discovery and Home Assistant entities."""

    frame: OpenWebNetFrame
    device_type: str | None = None
    state: str | None = None

    @property
    def who(self) -> str:
        return self.frame.who

    @property
    def what(self) -> str | None:
        return self.frame.what

    @property
    def where(self) -> str:
        return self.frame.where

    @property
    def dimension(self) -> str | None:
        return self.frame.dimension

    @property
    def values(self) -> tuple[str, ...]:
        return self.frame.values

    @property
    def raw(self) -> str:
        return self.frame.raw

    @property
    def key(self) -> str:
        return self.frame.key


_DEVICE_TYPES = {
    "0": "scene",
    "1": "light",
    "2": "cover",
    "3": "load",
    "4": "climate",
    "5": "alarm",
    "7": "intercom",
    "18": "energy",
}

_STATE_MAP = {
    "1": {"0": "off", "1": "on"},
    "2": {"0": "stopped", "1": "opening", "2": "closing"},
    "3": {"0": "off", "1": "on"},
    "4": {
        "0": "cool",
        "1": "heat",
        "102": "eco",
        "202": "eco",
        "302": "eco",
        "103": "off",
        "203": "off",
        "303": "off",
        "110": "heat",
        "210": "cool",
        "310": "auto",
        "111": "auto",
        "211": "auto",
        "311": "auto",
    },
    "5": {
        "0": "disarmed",
        "1": "armed_away",
        "3": "armed_home",
        "4": "triggered",
    },
}


def normalize_frame(frame: OpenWebNetFrame) -> NormalizedEvent:
    device_type = _DEVICE_TYPES.get(frame.who)
    state = None if frame.what is None else _STATE_MAP.get(frame.who, {}).get(frame.what)
    return NormalizedEvent(frame=frame, device_type=device_type, state=state)
