"""Tests for stable entity identity and device-aware naming."""
from __future__ import annotations

from custom_components.bticino_myhome.entity import BticinoEntity
from custom_components.bticino_myhome.gateway import BticinoGateway


def test_entity_unique_id_uses_persisted_gateway_identity() -> None:
    gateway = BticinoGateway("192.168.1.99", 20000, "", identity="192.168.1.20:20000")
    entity = BticinoEntity(gateway, "1", "21", "Kitchen")
    assert entity.unique_id == "192.168.1.20:20000:1:21"
    assert entity.has_entity_name is True
    assert entity.name is None
    assert entity.device_info["name"] == "Kitchen"
    assert ("bticino_myhome", "192.168.1.20:20000:1:21") in entity.device_info["identifiers"]
