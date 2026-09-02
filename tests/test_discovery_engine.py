from custom_components.bticino_myhome.discovery import BticinoDiscovery, DiscoverySource


def test_parse_light_event() -> None:
    device = BticinoDiscovery.parse_event("*1*1*21##")
    assert device is not None
    assert device.who == "1"
    assert device.where == "21"
    assert device.device_type == "light"
    assert device.source == DiscoverySource.PASSIVE.value
    assert "on_off" in device.capabilities


def test_parse_energy_event() -> None:
    device = BticinoDiscovery.parse_event("*18*1*31##")
    assert device is not None
    assert device.device_type == "energy"


def test_manual_unknown_who_is_allowed() -> None:
    device = BticinoDiscovery.from_manual(who="99", where="12", device_type="sensor", name="Sensore")
    assert device.key == "99-12"
    assert device.source == DiscoverySource.MANUAL.value
    assert device.device_type == "sensor"


def test_active_candidate_is_replaced_by_real_event() -> None:
    active = BticinoDiscovery.from_manual(who="1", where="21", device_type="light", name="Luce cucina")
    assert active.device_type == "light"
    event = BticinoDiscovery.parse_event("*1*0*21##")
    assert event is not None
    assert event.source == DiscoverySource.PASSIVE.value
