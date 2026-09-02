"""Discovery of OpenWebNet endpoints exposed by an MH201."""
from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import asdict, dataclass, field

from .const import (
    SCAN_TIMEOUT,
    SCENARIO_ADDRESS_RANGE,
    WHO_ALARM,
    WHO_AUTOMATION,
    WHO_LIGHTING,
    WHO_LOAD_MANAGEMENT,
    WHO_SCENARIO,
    WHO_VIDEO_DOOR_ENTRY,
)
from .gateway import BticinoGateway

_LOGGER = logging.getLogger(__name__)
_ADDRESS_RANGE = range(1, 100)
_FRAME_RE = re.compile(r"^\*(?P<who>\d+)\*(?P<what>[^*#]*)\*(?P<where>[^#]+)##$")


@dataclass(slots=True)
class DiscoveredDevice:
    who: str
    where: str
    device_type: str
    name: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def key(self) -> str:
        return f"{self.who}-{self.where}"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "DiscoveredDevice":
        return cls(
            who=str(data["who"]),
            where=str(data["where"]),
            device_type=str(data["device_type"]),
            name=str(data.get("name", "")),
            extra=dict(data.get("extra", {})),
        )


class BticinoDiscovery:
    """Discover endpoints by active status probes plus passive bus events."""

    def __init__(self, gateway: BticinoGateway) -> None:
        self._gateway = gateway
        self._found: dict[str, DiscoveredDevice] = {}
        self._unsubscribe = None

    async def async_passive_listen(self, listen_seconds: int = 15) -> list[DiscoveredDevice]:
        """Listen only to real bus traffic and learn supported devices.

        No OpenWebNet command is transmitted by this method. This is the safe
        discovery mode intended for physical-button learning: the user
        interacts with the BTicino installation while the MH201 reports the
        resulting events.
        """
        self._found.clear()
        self._unsubscribe = self._gateway.add_listener(self._on_event)
        try:
            _LOGGER.info("Passive learning OpenWebNet avviato per %ss", listen_seconds)
            await asyncio.sleep(max(1, min(int(listen_seconds), 120)))
            return list(self._found.values())
        finally:
            if self._unsubscribe:
                self._unsubscribe()
                self._unsubscribe = None

    @staticmethod
    def parse_event(raw_message: str) -> DiscoveredDevice | None:
        """Convert a supported OpenWebNet event into a discovery candidate."""
        match = _FRAME_RE.match(raw_message.strip())
        if not match:
            return None
        who = match.group("who")
        where = match.group("where")
        type_map = {
            WHO_SCENARIO: "scene",
            WHO_LIGHTING: "light",
            WHO_AUTOMATION: "cover",
            WHO_LOAD_MANAGEMENT: "load",
            WHO_ALARM: "alarm",
            WHO_VIDEO_DOOR_ENTRY: "intercom",
        }
        dtype = type_map.get(who)
        if dtype is None:
            return None
        return DiscoveredDevice(
            who=who,
            where=where,
            device_type=dtype,
            name=BticinoDiscovery.default_name(dtype, where),
            extra={"discovery": "passive", "what": match.group("what")},
        )

    @staticmethod
    def default_name(device_type: str, where: str) -> str:
        labels = {
            "light": "Luce",
            "cover": "Tapparella",
            "load": "Carico",
            "alarm": "Allarme",
            "intercom": "Citofono",
            "scene": "Scenario",
        }
        return f"{labels.get(device_type, device_type.capitalize())} {where}"

    async def async_run_full_scan(
        self, include_scenarios: bool = True, listen_seconds: int = SCAN_TIMEOUT
    ) -> list[DiscoveredDevice]:
        self._found.clear()
        self._unsubscribe = self._gateway.add_listener(self._on_event)
        try:
            await self._probe_lighting_and_automation()
            await self._probe_load_management()
            await self._probe_alarm_4200c()
            if include_scenarios:
                self._register_scenario_candidates()
            if listen_seconds > 0:
                _LOGGER.info(
                    "Discovery passiva per %ss: usa l'impianto durante la scansione "
                    "per far emergere eventuali dispositivi/eventi non interrogabili.",
                    listen_seconds,
                )
                await asyncio.sleep(listen_seconds)
            return list(self._found.values())
        finally:
            if self._unsubscribe:
                self._unsubscribe()
                self._unsubscribe = None

    async def _probe_lighting_and_automation(self) -> None:
        for where in _ADDRESS_RANGE:
            for who, dtype in ((WHO_LIGHTING, "light"), (WHO_AUTOMATION, "cover")):
                await self._probe(f"*#{who}*{where}##", who, str(where), dtype)

    async def _probe_load_management(self) -> None:
        for where in _ADDRESS_RANGE:
            await self._probe(
                f"*#{WHO_LOAD_MANAGEMENT}*{where}##",
                WHO_LOAD_MANAGEMENT,
                str(where),
                "load",
            )

    async def _probe_alarm_4200c(self) -> None:
        try:
            await self._gateway.async_send(f"*#{WHO_ALARM}*0##")
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Probe 4200C non riuscito: %s", err)

    async def _probe(self, frame: str, who: str, where: str, dtype: str) -> None:
        try:
            await self._gateway.async_send(frame)
            await asyncio.sleep(0.05)
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Probe %s non riuscito: %s", frame, err)
            return
        # Some gateways do not emit a useful response for every status query;
        # the passive listener remains authoritative for actual discovered nodes.
        return

    def _register_scenario_candidates(self) -> None:
        for addr in SCENARIO_ADDRESS_RANGE:
            device = DiscoveredDevice(
                who=WHO_SCENARIO,
                where=str(addr),
                device_type="scene",
                name=f"Scenario {addr}",
                extra={"candidate": True},
            )
            self._found.setdefault(device.key, device)

    def _on_event(self, raw_message: str) -> None:
        device = self.parse_event(raw_message)
        if device is None:
            return
        if device.key not in self._found:
            self._found[device.key] = device
            _LOGGER.info(
                "Discovery: trovato %s @ %s (%s)",
                device.device_type,
                device.where,
                device.extra.get("discovery", "active"),
            )
