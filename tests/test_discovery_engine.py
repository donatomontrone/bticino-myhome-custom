"""Tests for discovery mapping."""
from __future__ import annotations

from custom_components.bticino_myhome.discovery import BticinoDiscovery, DiscoverySource
from custom_components.bticino_myhome.protocol.thermoregulation import (
    CAPABILITY_COOLING,
    CAPABILITY_HEATING,
    CLIMATE_PROFILE_HEATING,
)


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
    assert CAPABILITY_HEATING not in device.capabilities
    assert CAPABILITY_COOLING not in device.capabilities


def test_parse_climate_heating_event_infers_heat_only_evidence() -> None:
    device = BticinoDiscovery.parse_event("*4*110*2##")
    assert device is not None
    assert CAPABILITY_HEATING in device.capabilities
    assert CAPABILITY_COOLING not in device.capabilities


def test_parse_climate_generic_event_infers_both_directions() -> None:
    device = BticinoDiscovery.parse_event("*4*311*2##")
    assert device is not None
    assert CAPABILITY_HEATING in device.capabilities
    assert CAPABILITY_COOLING in device.capabilities


def test_manual_climate_profile_persists_explicit_capability() -> None:
    device = BticinoDiscovery.from_manual(
        who="4",
        where="2",
        device_type="climate",
        name="Soggiorno",
        climate_profile=CLIMATE_PROFILE_HEATING,
    )
    assert CAPABILITY_HEATING in device.capabilities
    assert CAPABILITY_COOLING not in device.capabilities
    assert device.extra["climate_profile"] == CLIMATE_PROFILE_HEATING

    restored = type(device).from_dict(device.to_dict())
    assert restored.capabilities == device.capabilities
    assert restored.extra["climate_profile"] == CLIMATE_PROFILE_HEATING


def test_manual_unknown_who_is_allowed() -> None:
    device = BticinoDiscovery.from_manual(
        who="99", where="12", device_type="sensor", name="Sensor"
    )
    assert device.source == DiscoverySource.MANUAL.value
    assert device.device_type == "sensor"
