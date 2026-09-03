"""Runtime device registry for BTicino MyHome entities."""
from __future__ import annotations

from collections.abc import Callable, Iterable

from .discovery import DiscoveredDevice, DiscoverySource


class BticinoDeviceManager:
    """Manage device discovery and manual overrides."""

    def __init__(self, devices: Iterable[DiscoveredDevice] | None = None) -> None:
        self._devices: dict[str, DiscoveredDevice] = {}
        if devices:
            for device in devices:
                self._devices[device.key] = device

    def replace(self, devices: Iterable[DiscoveredDevice]) -> list[DiscoveredDevice]:
        """Merge discovered devices with manual overrides, notifying only changed."""
        changed: list[DiscoveredDevice] = []
        for device in devices:
            previous = self._devices.get(device.key)
            if previous is not None and previous.source == DiscoverySource.MANUAL.value:
                if device.source != DiscoverySource.MANUAL.value:
                    continue
            self._devices[device.key] = device
            changed.append(device)
        return changed

    def get(self, key: str) -> DiscoveredDevice | None:
        """Get a device by key."""
        return self._devices.get(key)

    def all(self) -> list[DiscoveredDevice]:
        """Get all devices."""
        return list(self._devices.values())

    def add_listener(self, callback: Callable[[list[DiscoveredDevice]], None]) -> Callable[[], None]:
        """Subscribe to device changes."""
        raise NotImplementedError("Listeners not yet implemented")
