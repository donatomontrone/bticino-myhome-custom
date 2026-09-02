"""Runtime device registry for BTicino MyHome entities."""
from __future__ import annotations

from collections.abc import Callable, Iterable

from .discovery import DiscoveredDevice


class BticinoDeviceManager:
    """Own the normalized BTicino device inventory for one config entry."""

    def __init__(self, devices: Iterable[DiscoveredDevice] = ()) -> None:
        self._devices: dict[str, DiscoveredDevice] = {device.key: device for device in devices}
        self._listeners: set[Callable[[DiscoveredDevice], None]] = set()

    @property
    def devices(self) -> list[DiscoveredDevice]:
        return [self._devices[key] for key in sorted(self._devices)]

    def get(self, key: str) -> DiscoveredDevice | None:
        return self._devices.get(key)

    def add(self, device: DiscoveredDevice) -> bool:
        previous = self._devices.get(device.key)
        self._devices[device.key] = device
        changed = previous != device
        if changed:
            for listener in tuple(self._listeners):
                listener(device)
        return changed

    def add_many(self, devices: Iterable[DiscoveredDevice]) -> int:
        """Merge candidates and return the number of changed entries."""
        return sum(self.add(device) for device in devices)

    def add_listener(self, callback: Callable[[DiscoveredDevice], None]) -> Callable[[], None]:
        self._listeners.add(callback)

        def _remove() -> None:
            self._listeners.discard(callback)

        return _remove

    def remove(self, key: str) -> bool:
        return self._devices.pop(key, None) is not None

    def replace(self, devices: Iterable[DiscoveredDevice]) -> None:
        devices = list(devices)
        self._devices = {device.key: device for device in devices}
        for device in devices:
            for listener in tuple(self._listeners):
                listener(device)

    def as_dicts(self) -> list[dict]:
        return [device.to_dict() for device in self.devices]
