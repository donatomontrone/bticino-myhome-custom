"""Runtime device registry for BTicino MyHome entities."""
from __future__ import annotations

from collections.abc import Callable, Iterable

from .discovery import DiscoverySource, DiscoveredDevice


class BticinoDeviceManager:
    """In-memory device inventory with listener notifications."""

    def __init__(self, devices: Iterable[DiscoveredDevice] = ()) -> None:
        self._devices: dict[str, DiscoveredDevice] = {device.key: device for device in devices}
        self._listeners: set[Callable[[DiscoveredDevice], None]] = set()

    @property
    def devices(self) -> list[DiscoveredDevice]:
        return list(self._devices.values())

    def get(self, key: str) -> DiscoveredDevice | None:
        return self._devices.get(key)

    def add(self, device: DiscoveredDevice) -> bool:
        """Add a device and notify listeners when the inventory changes.

        Explicitly configured manual devices have precedence over devices
        learned later from passive or active discovery.
        """
        previous = self._devices.get(device.key)
        if previous is not None and previous.source == DiscoverySource.MANUAL.value:
            if device.source != DiscoverySource.MANUAL.value:
                return False
        self._devices[device.key] = device
        changed = previous != device
        if changed:
            for listener in tuple(self._listeners):
                listener(device)
        return changed

    def add_listener(self, callback: Callable[[DiscoveredDevice], None]) -> Callable[[], None]:
        """Subscribe to newly added or updated devices."""
        self._listeners.add(callback)

        def _remove() -> None:
            self._listeners.discard(callback)

        return _remove

    def remove(self, key: str) -> bool:
        """Remove a device by key."""
        return self._devices.pop(key, None) is not None

    def replace(self, devices: Iterable[DiscoveredDevice]) -> None:
        """Replace the inventory with a new discovery result.

        Notifies listeners only for devices that are actually added or changed.
        Devices not in the new list are silently removed.
        """
        devices = list(devices)
        new_keys = {device.key for device in devices}

        for device in devices:
            self.add(device)

        for key in list(self._devices.keys()):
            if key not in new_keys:
                del self._devices[key]

    def as_dicts(self) -> list[dict]:
        """Return the inventory in ConfigEntry-safe form."""
        return [device.to_dict() for device in self.devices]
