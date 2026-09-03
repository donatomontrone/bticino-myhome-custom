"""Tests for translated secondary entity naming metadata."""
from __future__ import annotations

from custom_components.bticino_myhome.button import BticinoDoorLockRelease
from custom_components.bticino_myhome.gateway import BticinoGateway
from custom_components.bticino_myhome.sensor import BticinoDoorEntryEventLog


def test_secondary_entities_use_translation_keys() -> None:
    gateway = BticinoGateway("192.0.2.10", 20000, "", identity="gateway")

    release = BticinoDoorLockRelease(gateway, "6", "4000", "Entrance")
    raw_event = BticinoDoorEntryEventLog(gateway)

    assert release.has_entity_name is True
    assert release.translation_key == "door_release"
    assert raw_event.has_entity_name is True
    assert raw_event.translation_key == "door_entry_raw_event"
