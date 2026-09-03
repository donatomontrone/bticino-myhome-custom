"""BTicino MyHome discovery engine."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from OWNd.connection import OWNGateway

from .const import (
    WHO_ALARM,
    WHO_AUTOMATION,
    WHO_ENERGY_MANAGEMENT,
    WHO_LIGHTING,
    WHO_LOAD_MANAGEMENT,
    WHO_SCENARIO,
    WHO_VIDEO_DOOR_ENTRY,
)
from .gateway import BticinoGateway
from .protocol import NormalizedEvent

_LOGGER = logging.getLogger(__name__)


class DiscoverySource(str, Enum):
    """Source of device discovery."""

    PASSIVE = "passive"
    ACTIVE = "active"
    MANUAL = "manual"


@dataclass(frozen=True)
class DiscoveredDevice:
    """A discovered or manually configured device."""

    who: str
    address: str
    device_type: str
    capabilities: tuple[str, ...]
    source: str

    @property
    def key(self) -> str:
        return f"{self.who}_{self.address}"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DiscoveredDevice:
        return cls(
            who=str(data["who"]),
            address=str(data["address"]),
            device_type=str(data["device_type"]),
            capabilities=tuple(data.get("capabilities", [])),
            source=str(data.get("source", DiscoverySource.PASSIVE.value)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "who": self.who,
            "address": self.address,
            "device_type": self.device_type,
            "capabilities": list(self.capabilities),
            "source": self.source,
        }


class BticinoDiscovery:
    """Coordinate passive, active and manual discovery for one gateway."""

    _TYPE_MAP: dict[str, tuple[str, tuple[str, ...]]] = {
        WHO_SCENARIO: ("scene", ("activate",)),
        WHO_LIGHTING: ("light", ("on_off",)),
        WHO_AUTOMATION: ("cover", ("open_close",)),
        WHO_LOAD_MANAGEMENT: ("load", ("state",)),
        WHO_ALARM: ("alarm", ("arm_disarm", "events")),
        WHO_VIDEO_DOOR_ENTRY: ("intercom", ("events", "lock")),
        WHO_ENERGY_MANAGEMENT: ("energy", ("measurement",)),
    }

    def __init__(self, gateway: BticinoGateway) -> None:
        self._gateway = gateway
        self._devices: dict[str, DiscoveredDevice] = {}

    async def discover(self) -> list[DiscoveredDevice]:
        """Run active discovery and return devices."""
        devices: list[DiscoveredDevice] = []
        for who, (device_type, capabilities) in self._TYPE_MAP.items():
            frame = f"*{who}#*1#"
            try:
                await self._gateway.async_send(frame, is_status_request=True)
                await asyncio.sleep(0.05)
            except Exception as err:
                _LOGGER.debug("Probe %s failed: %s", frame, err)
            devices.append(
                DiscoveredDevice(
                    who=who,
                    address="0",
                    device_type=device_type,
                    capabilities=capabilities,
                    source=DiscoverySource.ACTIVE.value,
                )
            )
        return devices

    @classmethod
    async def discover_gateways(cls, timeout: int = 5) -> list[dict[str, Any]]:
        """Discover gateways on the network."""
        try:
            gateways = await OWNGateway.discover(timeout=timeout)
        except Exception as err:
            _LOGGER.warning("Gateway discovery failed: %s", err)
            return []

        result = []
        for gw in gateways:
            result.append({
                "host": gw.get("host"),
                "port": gw.get("port", 20000),
                "serial": gw.get("serial"),
                "model": gw.get("modelName") or "OpenWebNet Gateway",
                "manufacturer": gw.get("manufacturer"),
            })
        return [item for item in result if item["host"]]
