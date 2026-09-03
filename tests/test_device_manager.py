"""Tests for the runtime device manager."""
from __future__ import annotations

from custom_components.bticino_myhome.device import BticinoDeviceManager
from custom_components.bticino_myhome.discovery import DiscoveredDevice, DiscoverySource


def _device(where: str, source: str = DiscoverySource.PASSIVE.value) -> DiscoveredDevice:
    return DiscoveredDevice(
        who="1",
        where=where,
        device_type="light",
        name=f"Light {where}",
        capabilities=("on_off",),
        source=source,
    )


def test_replace_reports_only_actual_changes() -> None:
    manager = BticinoDeviceManager()
    first = _device("10")
    second = _device("11")
    assert manager.replace([first, second]) == [first, second]
    assert manager.replace([first, second]) == []


def test_manual_device_is_not_overwritten_or_dropped_by_discovery() -> None:
    manager = BticinoDeviceManager()
    manual = _device("10", DiscoverySource.MANUAL.value)
    passive = _device("10", DiscoverySource.PASSIVE.value)
    assert manager.add(manual) is True
    assert manager.add(passive) is False
    manager.replace([])
    assert manager.get(manual.key) == manual


def test_old_address_field_is_migrated_on_read() -> None:
    device = DiscoveredDevice.from_dict(
        {
            "who": "1",
            "address": "12",
            "device_type": "light",
            "source": "manual",
        }
    )
    assert device.where == "12"
