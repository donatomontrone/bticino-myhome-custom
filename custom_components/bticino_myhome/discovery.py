"""Discovery engine for BTicino MyHome / OpenWebNet devices."""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any, ClassVar

from OWNd.discovery import find_gateways

from .const import (
    DEFAULT_PORT,
    WHO_ALARM,
    WHO_AUTOMATION,
    WHO_ENERGY_MANAGEMENT,
    WHO_LIGHTING,
    WHO_LOAD_MANAGEMENT,
    WHO_SCENARIO,
    WHO_THERMOREGULATION,
    WHO_VIDEO_DOOR_ENTRY,
)
from .gateway import (
    BticinoGateway,
    BticinoGatewayCommandRejected,
    BticinoGatewayError,
)
from .protocol import NormalizedEvent, build_status_request, normalize_frame, parse_frame
from .protocol.thermoregulation import (
    CLIMATE_PROFILES,
    capabilities_for_climate_profile,
    capabilities_for_thermoregulation_state,
)

_LOGGER = logging.getLogger(__name__)
_ADDRESS_RANGE = range(1, 100)
_PROBE_INTERVAL = 0.05


class DiscoverySource(StrEnum):
    PASSIVE = "passive"
    ACTIVE = "active"
    MANUAL = "manual"


@dataclass(frozen=True, slots=True)
class DiscoveredGateway:
    """Normalized gateway information obtained from SSDP/OWNd discovery."""

    host: str
    port: int = DEFAULT_PORT
    serial: str | None = None
    udn: str | None = None
    model: str | None = None
    firmware: str | None = None
    manufacturer: str | None = None

    @property
    def identity(self) -> str:
        if self.serial:
            return f"serial:{self.serial.strip().lower()}"
        if self.udn:
            return f"udn:{self.udn.strip().lower()}"
        return f"{self.host.strip().lower()}:{self.port}"

    @classmethod
    def from_ownd(cls, data: dict[str, Any]) -> DiscoveredGateway | None:
        host = data.get("address") or data.get("host")
        if not host:
            return None
        return cls(
            host=str(host),
            port=int(data.get("port", DEFAULT_PORT)),
            serial=_optional_text(data.get("serialNumber") or data.get("serial")),
            udn=_optional_text(data.get("UDN") or data.get("udn")),
            model=_optional_text(data.get("modelName") or data.get("model")),
            firmware=_optional_text(data.get("modelNumber") or data.get("firmware")),
            manufacturer=_optional_text(data.get("manufacturer")),
        )


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


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
        cls,
        who: str,
        where: str,
        device_type: str,
        name: str = "",
        climate_profile: str | None = None,
    ) -> DiscoveredDevice:
        return BticinoDiscovery.from_manual(
            who=who,
            where=where,
            device_type=device_type,
            name=name,
            climate_profile=climate_profile,
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
    _ALLOWED_MANUAL_TYPES: ClassVar[dict[str, set[str]]] = {
        WHO_SCENARIO: {"scene"},
        WHO_LIGHTING: {"light"},
        WHO_AUTOMATION: {"cover"},
        WHO_LOAD_MANAGEMENT: {"load"},
        WHO_THERMOREGULATION: {"climate"},
        WHO_ALARM: {"alarm"},
        WHO_VIDEO_DOOR_ENTRY: {"intercom", "door_lock"},
        WHO_ENERGY_MANAGEMENT: {"energy"},
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
        climate_profile: str | None = None,
    ) -> DiscoveredDevice:
        who = str(who).strip()
        where = str(where).strip()
        if not who or not where:
            raise ValueError("WHO and WHERE are required")
        mapped_type, mapped_capabilities = cls._TYPE_MAP.get(
            who, (device_type or "unknown", ())
        )
        dtype = device_type or mapped_type
        allowed = cls._ALLOWED_MANUAL_TYPES.get(who)
        if allowed is not None and dtype not in allowed:
            raise ValueError(f"Device type {dtype!r} is not valid for WHO={who}")
        capabilities = mapped_capabilities
        extra: dict[str, Any] = {"discovery": DiscoverySource.MANUAL.value}
        if who == WHO_VIDEO_DOOR_ENTRY and dtype == "door_lock":
            capabilities = ("lock",)
        if (
            who == WHO_THERMOREGULATION
            and dtype == "climate"
            and climate_profile is not None
        ):
            profile = str(climate_profile).strip()
            if profile not in CLIMATE_PROFILES:
                raise ValueError(f"Unsupported climate profile: {profile}")
            capabilities = (
                *mapped_capabilities,
                *capabilities_for_climate_profile(profile),
            )
            extra["climate_profile"] = profile
        return DiscoveredDevice(
            who=who,
            where=where,
            device_type=dtype,
            name=name or cls.default_name(dtype, where),
            source=DiscoverySource.MANUAL.value,
            capabilities=tuple(capabilities),
            extra=extra,
        )

    async def async_passive_listen(
        self, listen_seconds: int = 15
    ) -> list[DiscoveredDevice]:
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
        """Run conservative response-correlated discovery."""
        self._found.clear()
        self._unsubscribe = self._gateway.add_event_listener(self._on_event)
        try:
            for where in _ADDRESS_RANGE:
                for who in (WHO_LIGHTING, WHO_AUTOMATION, WHO_LOAD_MANAGEMENT):
                    await self._probe_status(who, str(where))
            await self._probe_status(WHO_ALARM, "0")
            if listen_seconds > 0:
                await asyncio.sleep(max(1, min(int(listen_seconds), 60)))
            return self._sorted_found(include_scenarios=include_scenarios)
        finally:
            self._stop_listener()

    async def async_run_full_scan(
        self, include_scenarios: bool = False, listen_seconds: int = 30
    ) -> list[DiscoveredDevice]:
        return await self.async_active_scan(
            listen_seconds=listen_seconds,
            include_scenarios=include_scenarios,
        )

    async def _probe_status(self, who: str, where: str) -> None:
        """Probe one address and accept only responses from that exchange as active."""
        frame = build_status_request(who, where)
        try:
            result = await self._gateway.async_send(frame, is_status_request=True)
        except BticinoGatewayCommandRejected:
            await asyncio.sleep(_PROBE_INTERVAL)
            return
        except BticinoGatewayError:
            raise

        for raw in result.responses:
            device = self.parse_event(raw)
            if device is None or device.who != who or device.where != where:
                continue
            device.source = DiscoverySource.ACTIVE.value
            device.extra["discovery"] = DiscoverySource.ACTIVE.value
            self._found[device.key] = device
        await asyncio.sleep(_PROBE_INTERVAL)

    @classmethod
    def parse_event(cls, raw_message: str) -> DiscoveredDevice | None:
        frame = parse_frame(raw_message)
        if frame is None:
            return None
        return cls._device_from_event(normalize_frame(frame))

    @classmethod
    def _device_from_event(
        cls,
        event: NormalizedEvent,
        source: DiscoverySource = DiscoverySource.PASSIVE,
    ) -> DiscoveredDevice | None:
        mapped = cls._TYPE_MAP.get(event.who)
        if mapped is None:
            return None
        dtype, base_capabilities = mapped
        capabilities = tuple(base_capabilities)
        if event.who == WHO_THERMOREGULATION:
            capabilities = (
                *capabilities,
                *capabilities_for_thermoregulation_state(event.state),
            )
        return DiscoveredDevice(
            who=event.who,
            where=event.where,
            device_type=dtype,
            name=cls.default_name(dtype, event.where),
            source=source.value,
            capabilities=tuple(dict.fromkeys(capabilities)),
            extra={
                "discovery": source.value,
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
            "door_lock": "Apriporta",
            "scene": "Scenario",
            "energy": "Energia",
        }
        return f"{labels.get(device_type, device_type.capitalize())} {where}"

    def _on_event(self, event: NormalizedEvent) -> None:
        device = self._device_from_event(event)
        if device is None:
            return
        existing = self._found.get(device.key)
        if existing is None:
            self._found[device.key] = device
            return
        merged_capabilities = tuple(
            dict.fromkeys((*existing.capabilities, *device.capabilities))
        )
        if merged_capabilities != existing.capabilities:
            existing.capabilities = merged_capabilities
        existing.extra.update(device.extra)

    def _sorted_found(
        self, *, include_scenarios: bool = True
    ) -> list[DiscoveredDevice]:
        return [
            self._found[key]
            for key in sorted(self._found)
            if include_scenarios or self._found[key].who != WHO_SCENARIO
        ]

    def _stop_listener(self) -> None:
        if self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None

    @classmethod
    async def discover_gateways(cls, timeout: int = 5) -> list[DiscoveredGateway]:
        try:
            async with asyncio.timeout(max(1, int(timeout))):
                gateways = await find_gateways()
        except Exception as err:
            _LOGGER.warning("Gateway discovery failed: %s", err)
            return []

        result: list[DiscoveredGateway] = []
        for raw in gateways:
            if not isinstance(raw, dict):
                continue
            gateway = DiscoveredGateway.from_ownd(raw)
            if gateway is not None:
                result.append(gateway)
        return result

    @classmethod
    async def discover_gateway(
        cls, host: str, timeout: int = 5
    ) -> DiscoveredGateway | None:
        normalized_host = host.strip().lower()
        for gateway in await cls.discover_gateways(timeout=timeout):
            if gateway.host.strip().lower() == normalized_host:
                return gateway
        return None
