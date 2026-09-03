"""Tests for BticinoDeviceManager merge and lifecycle rules."""
from __future__ import annotations

from unittest.mock import MagicMock

from custom_components.bticino_myhome.device import BticinoDeviceManager
from custom_components.bticino_myhome.discovery import DiscoveredDevice, DiscoverySource


def _device(*, source: str = DiscoverySource.PASSIVE.value, name: str = "Light") -> DiscoveredDevice:
    return DiscoveredDevice(
        who="1",
        where="21",
        device_type="light",
        name=name,
        source=source,
    )


def test_manual_device_is_not_overwritten_by_discovery() -> None:
    manager = BticinoDeviceManager([_device(source=DiscoverySource.MANUAL.value, name="Kitchen")])
    assert manager.add(_device(name="Auto name")) is False
    assert manager.get("1-21").name == "Kitchen"


def test_listener_only_receives_actual_changes() -> None:
    manager = BticinoDeviceManager()
    listener = MagicMock()
    manager.add_listener(listener)
    device = _device()
    assert manager.add(device) is True
    listener.assert_called_once_with(device)
    listener.reset_mock()
    assert manager.add(device) is False
    listener.assert_not_called()


def test_remove_notifies_and_replace_never_drops_unobserved_devices() -> None:
    passive = _device()
    other = DiscoveredDevice(who="2", where="22", device_type="cover", name="Cover")
    manager = BticinoDeviceManager([passive, other])
    removed = MagicMock()
    manager.add_remove_listener(removed)

    assert manager.replace([passive]) == []
    assert manager.get(other.key) is other
    removed.assert_not_called()

    assert manager.remove(other.key) is True
    removed.assert_called_once_with(other)
    assert manager.remove(other.key) is False
