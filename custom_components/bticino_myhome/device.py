"""Device layer for BTicino MyHome integration."""
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN
from .discovery import DiscoveredDevice

_LOGGER = logging.getLogger(__name__)


@dataclass
class BticinoDevice:
    """Device representation for BTicino MyHome."""

    device_type: str
    device_id: str
    unique_id: str
    name: str
    where: str
    who: int

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.device_id)},
            name=self.name,
            manufacturer="BTicino",
            model=f"WHO={self.who}",
        )

    @classmethod
    def from_discovered(cls, discovered: DiscoveredDevice) -> BticinoDevice:
        """Create a device from a discovered device."""
        return cls(
            device_type=discovered.device_type,
            device_id=discovered.device_id,
            unique_id=discovered.unique_id,
            name=discovered.name,
            where=discovered.where,
            who=discovered.who,
        )


class BticinoDeviceManager:
    """Device manager for BTicino MyHome."""

    def __init__(self) -> None:
        """Initialize device manager."""
        self._devices: dict[str, BticinoDevice] = {}
        self._listeners: list[Callable[[BticinoDevice], None]] = []

    def add_listener(self, listener: Callable[[BticinoDevice], None]) -> None:
        """Add a listener for device changes."""
        self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[BticinoDevice], None]) -> None:
        """Remove a listener."""
        self._listeners.remove(listener)

    def add(self, device: BticinoDevice) -> None:
        """Add a device."""
        previous = self._devices.get(device.device_id)
        self._devices[device.device_id] = device

        # Only notify if changed
        if previous != device:
            for listener in tuple(self._listeners):
                listener(device)

    def replace(self, devices: list[BticinoDevice]) -> None:
        """Replace all devices."""
        devices = list(devices)
        previous_devices = self._devices.copy()
        self._devices = {device.device_id: device for device in devices}

        # Notify for all devices
        for device in devices:
            previous = previous_devices.get(device.device_id)
            if previous != device:
                for listener in tuple(self._listeners):
                    listener(device)

    @property
    def devices(self) -> list[BticinoDevice]:
        """Return all devices."""
        return list(self._devices.values())

    def get_device(self, device_id: str) -> BticinoDevice | None:
        """Get a device by ID."""
        return self._devices.get(device_id)
