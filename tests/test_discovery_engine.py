"""Tests for discovery mapping."""
from __future__ import annotations

from custom_components.bticino_myhome.discovery import BticinoDiscovery, DiscoverySource


def test_parse_light_event_uses_openwebnet_what_where_order() -> None:
    device = BticinoDiscovery.parse_event("*1*1*21##")
    assert device is not None
    assert device.who == "1"
    assert device.where == "21"
    assert device.device_type == "light"


def test_parse_climate_dimension_event() -> None:
    device = BticinoDiscovery.parse_event("*#4*2*0*0225##")
    assert device is not None
    assert device.who == "4"
    assert device.where == "2"
    assert device.device_type == "climate"


def test_manual_unknown_who_is_allowed() -> None:
    device = BticinoDiscovery.from_manual(
        who="99", where="12", device_type="sensor", name="Sensor"
    )
    assert device.source == DiscoverySource.MANUAL.value
    assert device.device_type == "sensor"
