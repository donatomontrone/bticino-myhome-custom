"""Runtime device registry for BTicino MyHome entities."""
from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from .discovery import DiscoveredDevice, DiscoverySource


class BticinoDeviceManager:
    """In-memory device inventory with explicit add/remove notifications."""

    def __init__(self, devices: Iterable[DiscoveredDevice] = ()) -> None:
        self._devices: dict[str, DiscoveredDevice] = {device.key: device for device in devices}
        self._listeners: set[Callable[[DiscoveredDevice], None]] = set()
        self._remove_listeners: set[Callable[[DiscoveredDevice], None]] = set()

    @property
    def devices(self) -> list[DiscoveredDevice]:
        return list(self._devices.values())

    def get(self, key: str) -> DiscoveredDevice | None:
        return self._devices.get(key)

    def add(self, device: DiscoveredDevice) -> bool:
        """Add/update a device while preserving explicit manual configuration."""
        previous = self._devices.get(device.key)
        if (
            previous is not None
            and previous.source == DiscoverySource.MANUAL.value
            and device.source != DiscoverySource.MANUAL.value
        ):
            return False
        if previous == device:
            return False
        self._devices[device.key] = device
        for listener in tuple(self._listeners):
            listener(device)
        return True

    def add_listener(self, callback: Callable[[DiscoveredDevice], None]) -> Callable[[], None]:
        self._listeners.add(callback)

        def _remove() -> None:
            self._listeners.discard(callback)

        return _remove

    def add_remove_listener(
        self, callback: Callable[[DiscoveredDevice], None]
    ) -> Callable[[], None]:
        """Subscribe to explicit inventory removals."""
        self._remove_listeners.add(callback)

        def _remove() -> None:
            self._remove_listeners.discard(callback)

        return _remove

    def remove(self, key: str) -> bool:
        """Explicitly remove one device and notify runtime consumers."""
        device = self._devices.pop(key, None)
        if device is None:
            return False
        for listener in tuple(self._remove_listeners):
            listener(device)
        return True

    def replace(self, devices: Iterable[DiscoveredDevice]) -> list[DiscoveredDevice]:
        """Merge a discovery snapshot without treating absence as removal.

        OpenWebNet discovery is observational and may be incomplete. A device is
        therefore removed only through ``remove`` after an explicit user action.
        """
        changed: list[DiscoveredDevice] = []
        for device in devices:
            if self.add(device):
                changed.append(device)
        return changed

    def as_dicts(self) -> list[dict[str, Any]]:
        return [device.to_dict() for device in self.devices]
