"""Runtime device registry for BTicino MyHome entities."""
from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

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
        """Add/update a device while preserving explicit manual configuration."""
        previous = self._devices.get(device.key)
        if (
            previous is not None
            and previous.source == DiscoverySource.MANUAL.value
            and device.source != DiscoverySource.MANUAL.value
        ):
            return False
        changed = previous != device
        if not changed:
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

    def remove(self, key: str) -> bool:
        return self._devices.pop(key, None) is not None

    def replace(self, devices: Iterable[DiscoveredDevice]) -> list[DiscoveredDevice]:
        """Merge a discovery snapshot and return only actually changed devices.

        Manual devices survive discovery snapshots even when they are absent
        from the new result.
        """
        incoming = list(devices)
        incoming_keys = {device.key for device in incoming}
        changed: list[DiscoveredDevice] = []
        for device in incoming:
            if self.add(device):
                changed.append(device)

        for key, current in list(self._devices.items()):
            if key not in incoming_keys and current.source != DiscoverySource.MANUAL.value:
                del self._devices[key]
        return changed

    def as_dicts(self) -> list[dict[str, Any]]:
        return [device.to_dict() for device in self.devices]
