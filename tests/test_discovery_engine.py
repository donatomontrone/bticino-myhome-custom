"""Tests for discovery engine."""
from custom_components.bticino_myhome.discovery import BticinoDiscovery, DiscoveredDevice, DiscoverySource


def test_parse_light_event() -> None:
    """Verify light event parsing."""
    # Frame: *WHO*WHERE*DIM## = *1*1*21##
    # WHO=1 (lighting), WHERE=1 (address), DIM=21 (dimension/data)
    device = BticinoDiscovery.parse_event("*1*1*21##")
    assert device is not None
    assert device.address == "1"  # WHERE is the address
    assert device.device_type == "light"
    assert device.who == "1"


def test_parse_energy_event() -> None:
    """Verify energy event parsing."""
    # Frame: *WHO*WHERE*DIM## = *18*1*31##
    # WHO=18 (energy), WHERE=1 (address), DIM=31 (dimension/data)
    device = BticinoDiscovery.parse_event("*18*1*31##")
    assert device is not None
    assert device.address == "1"  # WHERE is the address
    assert device.device_type == "energy"
    assert device.who == "18"


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
