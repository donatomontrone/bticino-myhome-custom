"""Test device manager."""
from __future__ import annotations

from custom_components.bticino_myhome.device import BticinoDeviceManager
from custom_components.bticino_myhome.discovery import DiscoveredDevice


def test_replace_notifies_only_changed_devices() -> None:
    """Verify replace() notifies listeners only for added/changed devices."""
    initial = [
        DiscoveredDevice(who="1", where="1", device_type="light", name="Light 1"),
        DiscoveredDevice(who="1", where="2", device_type="light", name="Light 2"),
    ]
    manager = BticinoDeviceManager(initial)

    notified = []
    manager.add_listener(notified.append)

    manager.replace(initial)
    assert len(notified) == 0, "replace() should not notify for unchanged devices"

    changed = [
        DiscoveredDevice(who="1", where="1", device_type="light", name="Light 1 Updated"),
        DiscoveredDevice(who="1", where="2", device_type="light", name="Light 2"),
    ]
    manager.replace(changed)
    assert len(notified) == 1, "replace() should notify only for changed devices"
    assert notified[0].where == "1"
    assert notified[0].name == "Light 1 Updated"

    with_new = [
        DiscoveredDevice(who="1", where="1", device_type="light", name="Light 1 Updated"),
        DiscoveredDevice(who="1", where="2", device_type="light", name="Light 2"),
        DiscoveredDevice(who="1", where="3", device_type="light", name="Light 3"),
    ]
    notified.clear()
    manager.replace(with_new)
    assert len(notified) == 1, "replace() should notify for newly added devices"
    assert notified[0].where == "3"

    fewer = [
        DiscoveredDevice(who="1", where="1", device_type="light", name="Light 1 Updated"),
    ]
    notified.clear()
    manager.replace(fewer)
    assert len(notified) == 0, "replace() should not notify for removed devices"
    assert len(manager.devices) == 1
    assert manager.devices[0].where == "1"


def test_manual_device_not_overwritten_by_passive_event() -> None:
    """Verify manually added devices are not overwritten by passive events with same key."""
    manager = BticinoDeviceManager()

    manual = DiscoveredDevice(
        who="1", where="1", device_type="light", name="Manual Light",
        extra={"source": "manual"}
    )
    manager.add(manual)

    passive = DiscoveredDevice(
        who="1", where="1", device_type="light", name="Passive Light",
        extra={"source": "passive"}
    )

    manager.add(passive)

    assert manager.get("1-1").name == "Passive Light"
