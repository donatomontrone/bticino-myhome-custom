"""Discovery logic for BTicino MyHome integration."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from .protocol import WHO_THERMOREGULATION

_LOGGER = logging.getLogger(__name__)


@dataclass
class DiscoveredDevice:
    """Discovered device representation."""

    device_type: str
    device_id: str
    unique_id: str
    name: str
    where: str
    who: int

    @classmethod
    def from_manual(
        cls,
        device_type: str,
        device_id: str,
        unique_id: str,
        name: str,
        where: str,
        who: int,
    ) -> DiscoveredDevice:
        """Create a discovered device from manual configuration."""
        return cls(
            device_type=device_type,
            device_id=device_id,
            unique_id=unique_id,
            name=name,
            where=where,
            who=who,
        )


class BticinoDiscovery:
    """Discovery engine for BTicino MyHome devices."""

    def __init__(self) -> None:
        """Initialize discovery."""
        self._candidates: dict[str, DiscoveredDevice] = {}

    def process_event(self, who: int, where: str) -> DiscoveredDevice | None:
        """Process an OpenWebNet event and return discovered device if any."""
        # Thermoregulation (WHO=4)
        if who == WHO_THERMOREGULATION:
            return self._process_thermo(where)

        # Add other WHO handlers here
        return None

    def _process_thermo(self, where: str) -> DiscoveredDevice | None:
        """Process WHO=4 event."""
        device_id = f"thermo_{where}"

        # Check if already discovered
        if device_id in self._candidates:
            return self._candidates[device_id]

        # Create new device
        device = DiscoveredDevice(
            device_type="climate",
            device_id=device_id,
            unique_id=f"bticino_thermo_{where}",
            name=f"Thermostat {where}",
            where=where,
            who=WHO_THERMOREGULATION,
        )

        self._candidates[device_id] = device
        return device

    def get_candidates(self) -> list[DiscoveredDevice]:
        """Return all discovered candidates."""
        return list(self._candidates.values())

    def clear(self) -> None:
        """Clear all candidates."""
        self._candidates.clear()
