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
    def what(self) -> str:
        return self.frame.what

    @property
    def where(self) -> str:
        return self.frame.where

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
    "5": "alarm",
    "7": "intercom",
    "18": "energy",
}

_STATE_MAP = {
    "1": {"0": "off", "1": "on"},
    "2": {"1": "open", "2": "closed", "0": "stopped"},
    "3": {"0": "off", "1": "on"},
    "5": {
        "0": "disarmed",
        "1": "armed_away",
        "3": "armed_home",
        "4": "triggered",
    },
}


def normalize_frame(frame: OpenWebNetFrame) -> NormalizedEvent:
    """Normalize one parsed frame without making assumptions about HA."""
    device_type = _DEVICE_TYPES.get(frame.who)
    state = _STATE_MAP.get(frame.who, {}).get(frame.what)
    return NormalizedEvent(frame=frame, device_type=device_type, state=state)
