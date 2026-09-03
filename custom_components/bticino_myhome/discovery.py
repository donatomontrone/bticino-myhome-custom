"""Discovery engine for BTicino MyHome / OpenWebNet devices."""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any, ClassVar

from OWNd.connection import OWNGateway

from .const import (
    SCAN_TIMEOUT,
    SCENARIO_ADDRESS_RANGE,
    WHO_ALARM,
    WHO_AUTOMATION,
    WHO_ENERGY_MANAGEMENT,
    WHO_LIGHTING,
    WHO_LOAD_MANAGEMENT,
    WHO_SCENARIO,
    WHO_THERMOREGULATION,
    WHO_VIDEO_DOOR_ENTRY,
)
from .gateway import BticinoGateway
from .protocol import NormalizedEvent, build_status_request, normalize_frame, parse_frame

_LOGGER = logging.getLogger(__name__)
_ADDRESS_RANGE = range(1, 100)


class DiscoverySource(StrEnum):
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
    def from_dict(cls, data: dict[str, Any]) -> DiscoveredDevice:
        # ``address`` was emitted by an intermediate 0.1.13 implementation;
        # accepting it here keeps existing ConfigEntries migratable.
        where = data.get("where", data.get("address", ""))
        return cls(
            who=str(data["who"]),
            where=str(where),
            device_type=str(data["device_type"]),
            name=str(data.get("name", "")),
            source=str(data.get("source", DiscoverySource.MANUAL.value)),
            capabilities=tuple(str(item) for item in data.get("capabilities", [])),
            extra=dict(data.get("extra", {})),
        )

    @classmethod
    def from_manual(
        cls, who: str, where: str, device_type: str, name: str = ""
    ) -> DiscoveredDevice:
        return BticinoDiscovery.from_manual(
            who=who, where=where, device_type=device_type, name=name
        )


class BticinoDiscovery:
    """Coordinate passive, active and manual discovery for one gateway."""

    _TYPE_MAP: ClassVar[dict[str, tuple[str, tuple[str, ...]]]] = {
        WHO_SCENARIO: ("scene", ("activate",)),
        WHO_LIGHTING: ("light", ("on_off",)),
        WHO_AUTOMATION: ("cover", ("open_close",)),
        WHO_LOAD_MANAGEMENT: ("load", ("state",)),
        WHO_THERMOREGULATION: ("climate", ("temperature", "setpoint", "mode")),
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
        """Run conservative event-confirmed discovery.

        WHO=4 is intentionally passive-only here: until real MH201 captures are
        available we do not brute-force thermoregulation addresses.
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
        return await self.async_active_scan(
            listen_seconds=listen_seconds,
            include_scenarios=include_scenarios,
        )

    async def _probe_status(self, who: str, where: str) -> None:
        frame = build_status_request(who, where)
        try:
            await self._gateway.async_send(frame, is_status_request=True)
            await asyncio.sleep(0.05)
        except Exception as err:
            _LOGGER.debug("Probe %s failed: %s", frame, err)

    @classmethod
    def parse_event(cls, raw_message: str) -> DiscoveredDevice | None:
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
                "dimension": event.dimension,
                "state": event.state,
            },
        )

    @staticmethod
    def default_name(device_type: str, where: str) -> str:
        labels = {
            "light": "Luce",
            "cover": "Tapparella",
            "load": "Gestione carichi",
            "climate": "Termostato",
            "alarm": "Allarme",
            "intercom": "Citofono",
            "scene": "Scenario",
            "energy": "Energia",
        }
        return f"{labels.get(device_type, device_type.capitalize())} {where}"

    def _register_scenario_candidates(self) -> None:
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
        if existing is None or existing.source == DiscoverySource.ACTIVE.value:
            if existing is not None:
                device.name = existing.name
            self._found[device.key] = device

    def _sorted_found(self) -> list[DiscoveredDevice]:
        return [self._found[key] for key in sorted(self._found)]

    def _stop_listener(self) -> None:
        if self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None

    @classmethod
    async def discover_gateways(cls, timeout: int = 5) -> list[dict[str, Any]]:
        try:
            gateways = await OWNGateway.discover(timeout=timeout)
        except Exception as err:
            _LOGGER.warning("Gateway discovery failed: %s", err)
            return []

        result: list[dict[str, Any]] = []
        for gateway in gateways:
            if isinstance(gateway, dict):
                host = gateway.get("address") or gateway.get("host")
                port = gateway.get("port", 20000)
                serial = gateway.get("serial") or gateway.get("serialNumber")
                model = gateway.get("modelName") or "OpenWebNet Gateway"
                manufacturer = gateway.get("manufacturer")
            else:
                host = getattr(gateway, "address", None) or getattr(gateway, "host", None)
                port = getattr(gateway, "port", 20000)
                serial = getattr(gateway, "serial", None)
                model = getattr(gateway, "modelName", None) or "OpenWebNet Gateway"
                manufacturer = getattr(gateway, "manufacturer", None)
            if host:
                result.append(
                    {
                        "host": host,
                        "port": port,
                        "serial": serial,
                        "model": model,
                        "manufacturer": manufacturer,
                    }
                )
        return result
