"""Tests for translated secondary entity naming metadata."""
from __future__ import annotations

from custom_components.bticino_myhome.binary_sensor import BticinoIntercomCallSensor
from custom_components.bticino_myhome.button import BticinoDoorLockRelease
from custom_components.bticino_myhome.gateway import BticinoGateway
from custom_components.bticino_myhome.sensor import BticinoIntercomEventLog


def test_secondary_entities_use_translation_keys() -> None:
    gateway = BticinoGateway("192.0.2.10", 20000, "", identity="gateway")

    call = BticinoIntercomCallSensor(gateway, "7", "1", "Entrance")
    release = BticinoDoorLockRelease(gateway, "7", "1", "Entrance")
    raw_event = BticinoIntercomEventLog(gateway)

    assert call.has_entity_name is True
    assert call.translation_key == "intercom_call"
    assert release.has_entity_name is True
    assert release.translation_key == "door_release"
    assert raw_event.has_entity_name is True
    assert raw_event.translation_key == "who7_raw_event"
