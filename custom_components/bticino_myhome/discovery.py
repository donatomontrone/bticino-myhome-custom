"""Discovery engine for BTicino MyHome / OpenWebNet devices.

Discovery is deliberately split into three sources:
- passive: observe real OpenWebNet events from the MH201;
- active: send safe status probes and accept only devices confirmed by an event;
- manual: explicitly register a WHO/WHERE endpoint from the UI.

All sources produce the same ``DiscoveredDevice`` model.  The Device Manager
is therefore independent from how a device was discovered.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any

from .const import (
    SCAN_TIMEOUT,
    SCENARIO_ADDRESS_RANGE,
    WHO_ALARM,
    WHO_AUTOMATION,
    WHO_ENERGY_MANAGEMENT,
    WHO_LIGHTING,
    WHO_LOAD_MANAGEMENT,
    WHO_SCENARIO,
    WHO_VIDEO_DOOR_ENTRY,
)
from .gateway import BticinoGateway
from .protocol import NormalizedEvent, build_status_request, normalize_frame, parse_frame

_LOGGER = logging.getLogger(__name__)
_ADDRESS_RANGE = range(1, 100)


class DiscoverySource(StrEnum):
    """How a device was discovered."""

    PASSIVE = "passive"
    ACTIVE = "active"
    MANUAL = "manual"


@dataclass(slots=True)
class DiscoveredDevice:
    """Normalized device candidate shared by all discovery mechanisms."""

    who: str
    where: str
    device_type: str
    name: str = ""
    source: str = DiscoverySource.PASSIVE.value
    capabilities: tuple[str, ...] = ()
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> str:
        return f"{self.who}-{self.where}"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["capabilities"] = list(self.capabilities)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DiscoveredDevice":
        return cls(
            who=str(data["who"]),
            where=str(data["where"]),
            device_type=str(data["device_type"]),
            name=str(data.get("name", "")),
            source=str(data.get("source", DiscoverySource.MANUAL.value)),
            capabilities=tuple(str(item) for item in data.get("capabilities", [])),
            extra=dict(data.get("extra", {})),
        )


class BticinoDiscovery:
    """Coordinate passive, active and manual discovery for one gateway."""

    _TYPE_MAP = {
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
        self._found: dict[str, DiscoveredDevice] = {}
        self._unsubscribe: Callable[[], None] | None = None

    @classmethod
    def from_manual(
        cls,
        *,
        who: str,
        where: str,
        device_type: str | None = None,
        name: str | None = None,
    ) -> DiscoveredDevice:
        """Create a normalized candidate from explicit user configuration."""
        who = str(who).strip()
        where = str(where).strip()
        dtype, capabilities = cls._TYPE_MAP.get(who, (device_type or "unknown", ()))
        dtype = device_type or dtype
        return DiscoveredDevice(
            who=who,
            where=where,
            device_type=dtype,
            name=name or cls.default_name(dtype, where),
            source=DiscoverySource.MANUAL.value,
            capabilities=tuple(capabilities),
            extra={"discovery": DiscoverySource.MANUAL.value},
        )

    async def async_passive_listen(self, listen_seconds: int = 15) -> list[DiscoveredDevice]:
        """Listen only to real bus traffic; no command is transmitted."""
        self._found.clear()
        self._unsubscribe = self._gateway.add_event_listener(self._on_event)
        try:
            seconds = max(1, min(int(listen_seconds), 120))
            _LOGGER.info("Passive OpenWebNet learning started for %ss", seconds)
            await asyncio.sleep(seconds)
            return self._sorted_found()
        finally:
            self._stop_listener()

    async def async_active_scan(
        self,
        *,
        listen_seconds: int = 10,
        include_scenarios: bool = False,
    ) -> list[DiscoveredDevice]:
        """Probe supported WHO/WHERE ranges and accept only event-confirmed devices.

        OWNd's command API intentionally hides the raw response.  Therefore an
        active probe is never treated as proof of existence by itself: a device
        enters the inventory only if the MH201 emits a corresponding event while
        the probe/listening window is active. This avoids manufacturing false
        positives for empty addresses.
        """
        self._found.clear()
        self._unsubscribe = self._gateway.add_event_listener(self._on_event)
        try:
            for where in _ADDRESS_RANGE:
                for who in (WHO_LIGHTING, WHO_AUTOMATION, WHO_LOAD_MANAGEMENT):
                    await self._probe_status(who, str(where))
            await self._probe_status(WHO_ALARM, "0")
            if include_scenarios:
                self._register_scenario_candidates()
            if listen_seconds > 0:
                await asyncio.sleep(max(1, min(int(listen_seconds), 60)))
            return self._sorted_found()
        finally:
            self._stop_listener()

    async def async_run_full_scan(
        self, include_scenarios: bool = True, listen_seconds: int = SCAN_TIMEOUT
    ) -> list[DiscoveredDevice]:
        """Run the conservative active scan followed by an observation window."""
        return await self.async_active_scan(
            listen_seconds=listen_seconds,
            include_scenarios=include_scenarios,
        )

    async def _probe_status(self, who: str, where: str) -> None:
        # OpenWebNet status-query syntax varies by WHO. Keep the probe isolated;
        # receiving a matching event is the only thing that confirms discovery.
        frame = build_status_request(who, where)
        try:
            await self._gateway.async_send(frame)
            await asyncio.sleep(0.05)
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Probe %s failed: %s", frame, err)

    @classmethod
    def parse_event(cls, raw_message: str) -> DiscoveredDevice | None:
        """Compatibility helper: parse a raw event through the protocol layer."""
        frame = parse_frame(raw_message)
        if frame is None:
            return None
        return cls._device_from_event(normalize_frame(frame))

    @classmethod
    def _device_from_event(cls, event: NormalizedEvent) -> DiscoveredDevice | None:
        mapped = cls._TYPE_MAP.get(event.who)
        if mapped is None:
            return None
        dtype, capabilities = mapped
        return DiscoveredDevice(
            who=event.who,
            where=event.where,
            device_type=dtype,
            name=cls.default_name(dtype, event.where),
            source=DiscoverySource.PASSIVE.value,
            capabilities=tuple(capabilities),
            extra={
                "discovery": DiscoverySource.PASSIVE.value,
                "what": event.what,
                "state": event.state,
            },
        )

    @staticmethod
    def default_name(device_type: str, where: str) -> str:
        labels = {
            "light": "Luce",
            "cover": "Tapparella",
            "load": "Gestione carichi",
            "alarm": "Allarme",
            "intercom": "Citofono",
            "scene": "Scenario",
            "energy": "Energia",
        }
        return f"{labels.get(device_type, device_type.capitalize())} {where}"

    def _register_scenario_candidates(self) -> None:
        # Scenarios are virtual endpoints. Unlike physical devices, they can be
        # useful as explicit candidates even without a bus event.
        for addr in SCENARIO_ADDRESS_RANGE:
            device = DiscoveredDevice(
                who=WHO_SCENARIO,
                where=str(addr),
                device_type="scene",
                name=f"Scenario {addr}",
                source=DiscoverySource.ACTIVE.value,
                capabilities=("activate",),
                extra={"candidate": True, "discovery": DiscoverySource.ACTIVE.value},
            )
            self._found.setdefault(device.key, device)

    def _on_event(self, event: NormalizedEvent) -> None:
        device = self._device_from_event(event)
        if device is None:
            return
        existing = self._found.get(device.key)
        if existing is None:
            self._found[device.key] = device
            _LOGGER.info(
                "Discovery: found %s @ %s (%s)",
                device.device_type,
                device.where,
                device.source,
            )
        else:
            # A real event is stronger evidence than a generic active candidate.
            if existing.source == DiscoverySource.ACTIVE.value:
                device.name = existing.name
                self._found[device.key] = device

    def _sorted_found(self) -> list[DiscoveredDevice]:
        return [self._found[key] for key in sorted(self._found)]

    def _stop_listener(self) -> None:
        if self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None
