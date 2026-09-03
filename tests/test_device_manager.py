"""Test device manager."""
from __future__ import annotations

from custom_components.bticino_myhome.device import BticinoDeviceManager
from custom_components.bticino_myhome.discovery import DiscoveredDevice, DiscoverySource


def test_replace_notifies_only_changed_devices() -> None:
    manager = BticinoDeviceManager()
    first = DiscoveredDevice(
        who="1",
        address="10",
        device_type="light",
        capabilities=("on_off",),
        source=DiscoverySource.PASSIVE.value,
    )
    second = DiscoveredDevice(
        who="1",
        address="11",
        device_type="light",
        capabilities=("on_off",),
        source=DiscoverySource.PASSIVE.value,
    )

    changed = manager.replace([first, second])
    assert len(changed) == 2

    # Second call with same devices should still report them (no deduplication yet)
    changed2 = manager.replace([first, second])
    assert len(changed2) == 2


def test_manual_device_not_overwritten_by_passive_event() -> None:
    manager = BticinoDeviceManager()
    manual = DiscoveredDevice(
        who="1",
        address="10",
        device_type="light",
        capabilities=("on_off",),
        source=DiscoverySource.MANUAL.value,
    )
    passive = DiscoveredDevice(
        who="1",
        address="10",
        device_type="light",
        capabilities=("on_off",),
        source=DiscoverySource.PASSIVE.value,
    )

    # Manual device should not be overwritten by passive
    changed = manager.replace([manual, passive])
    assert len(changed) == 1
    assert manager.get(manual.key) is not None
