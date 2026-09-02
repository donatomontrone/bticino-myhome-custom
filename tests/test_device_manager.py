from custom_components.bticino_myhome.device import BticinoDeviceManager
from custom_components.bticino_myhome.discovery import DiscoveredDevice


def make_device(who: str, where: str, device_type: str) -> DiscoveredDevice:
    return DiscoveredDevice(who=who, where=where, device_type=device_type)


def test_device_manager_add_replace_and_remove() -> None:
    first = make_device("1", "2", "light")
    second = make_device("2", "3", "cover")
    manager = BticinoDeviceManager([first])

    assert manager.get("1-2") == first
    assert manager.add(second) is True
    assert {device.key for device in manager.devices} == {"1-2", "2-3"}

    updated = make_device("1", "2", "light")
    updated.name = "Kitchen"
    assert manager.add(updated) is True
    assert manager.get("1-2").name == "Kitchen"

    manager.replace([second])
    assert manager.get("1-2") is None
    assert manager.get("2-3") == second
    assert manager.remove("2-3") is True
    assert manager.remove("2-3") is False


def test_device_manager_replace_notifies_only_changed_or_new() -> None:
    first = make_device("1", "2", "light")
    second = make_device("2", "3", "cover")
    manager = BticinoDeviceManager([first])
    notifications = []
    manager.add_listener(notifications.append)

    manager.replace([first])
    assert notifications == []

    updated = make_device("1", "2", "light")
    updated.name = "Kitchen"
    manager.replace([updated, second])
    assert [device.key for device in notifications] == ["1-2", "2-3"]
    assert manager.get("1-2") == updated
    assert manager.get("2-3") == second

    notifications.clear()
    manager.replace([updated, second])
    assert notifications == []
