"""Tests for protocol-family scope decisions."""
from __future__ import annotations

import pytest

from custom_components.bticino_myhome.discovery import BticinoDiscovery


def test_who3_is_rejected_from_manual_inventory() -> None:
    with pytest.raises(ValueError):
        BticinoDiscovery.from_manual(
            who="3", where="1", device_type="load", name="Legacy load"
        )


def test_who6_door_entry_can_be_registered_manually() -> None:
    device = BticinoDiscovery.from_manual(
        who="6", where="4000", device_type="intercom", name="HomeTouch"
    )
    assert device.device_type == "intercom"
    assert "lock" in device.capabilities


def test_who7_multimedia_is_not_misclassified_as_door_entry() -> None:
    assert BticinoDiscovery.parse_event("*7*0*4000##") is None
