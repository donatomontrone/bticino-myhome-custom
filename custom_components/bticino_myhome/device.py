"""Runtime device registry for BTicino MyHome entities."""
from __future__ import annotations

from collections.abc import Iterable

from .discovery import DiscoveredDevice


class BticinoDeviceManager:
    """Own the discovered BTicino device inventory for one config entry."""

    def __init__(self, devices: Iterable[DiscoveredDevice] = ()) -> None:
        self._devices: dict[str, DiscoveredDevice] = {device.key: device for device in devices}

    @property
    def devices(self) -> list[DiscoveredDevice]:
        """Return devices in deterministic key order."""
        return [self._devices[key] for key in sorted(self._devices)]

    def get(self, key: str) -> DiscoveredDevice | None:
        """Return a device by its stable WHO/WHERE key."""
        return self._devices.get(key)

    def add(self, device: DiscoveredDevice) -> bool:
        """Add a device and report whether the inventory changed."""
        previous = self._devices.get(device.key)
        self._devices[device.key] = device
        return previous != device

    def remove(self, key: str) -> bool:
        """Remove a device by key."""
        return self._devices.pop(key, None) is not None

    def replace(self, devices: Iterable[DiscoveredDevice]) -> None:
        """Replace the inventory with a new discovery result."""
        self._devices = {device.key: device for device in devices}

    def as_dicts(self) -> list[dict]:
        """Return the inventory in ConfigEntry-safe form."""
        return [device.to_dict() for device in self.devices]
