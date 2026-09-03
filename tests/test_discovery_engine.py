"""Tests for discovery engine."""
from custom_components.bticino_myhome.discovery import BticinoDiscovery, DiscoveredDevice, DiscoverySource


def test_parse_light_event() -> None:
    """Verify light event parsing."""
    device = BticinoDiscovery.parse_event("*1*1*21##")
    assert device is not None
    assert device.address == "21"
    assert device.device_type == "light"


def test_parse_energy_event() -> None:
    """Verify energy event parsing."""
    device = BticinoDiscovery.parse_event("*18*1*31##")
    assert device is not None
    assert device.address == "31"
    assert device.device_type == "energy"


def test_manual_unknown_who_is_allowed() -> None:
    """Verify manual devices can be created for unknown WHO."""
    device = DiscoveredDevice.from_manual(who="99", where="12", device_type="sensor", name="Sensore")
    assert device is not None
    assert device.who == "99"
    assert device.address == "12"
    assert device.source == DiscoverySource.MANUAL.value


def test_active_candidate_is_replaced_by_real_event() -> None:
    """Verify active candidate is replaced by real event."""
    active = DiscoveredDevice.from_manual(who="1", where="21", device_type="light", name="Luce cucina")
    assert active is not None
    assert active.who == "1"
    assert active.address == "21"


def test_manual_device_is_not_overwritten_by_passive_event() -> None:
    """Verify manual device is not overwritten by passive event."""
    manual = DiscoveredDevice.from_manual(
        who="1",
        where="10",
        device_type="light",
        name="Luce manuale",
    )
    assert manual is not None
    assert manual.source == DiscoverySource.MANUAL.value
