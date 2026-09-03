"""Shared entity helpers."""
from __future__ import annotations

from collections.abc import Callable

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .gateway import BticinoGateway
from .protocol import NormalizedEvent


class BticinoEntity(Entity):
    """Base entity with gateway availability and endpoint metadata."""

    _attr_should_poll = False

    def __init__(self, gateway: BticinoGateway, who: str, where: str, name: str) -> None:
        self._gateway = gateway
        self._who = str(who)
        self._where = str(where)
        self._attr_name = name or f"BTicino {who}/{where}"
        self._attr_unique_id = f"{gateway.host}:{gateway.port}:{self._who}:{self._where}"
        self._attr_available = gateway.connected
        self._unsubscribe_event: Callable[[], None] | None = None
        self._unsubscribe_connection: Callable[[], None] | None = None

    @property
    def gateway(self) -> BticinoGateway:
        return self._gateway

    @property
    def who(self) -> str:
        return self._who

    @property
    def where(self) -> str:
        return self._where

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(
                DOMAIN,
                f"{self._gateway.host}:{self._gateway.port}:{self._who}:{self._where}",
            )},
            name=self._attr_name,
            manufacturer="BTicino / Legrand",
            model=f"MyHome OpenWebNet WHO={self._who}",
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._unsubscribe_connection = self._gateway.add_connection_listener(
            self._handle_connection_state
        )
        self._unsubscribe_event = self._gateway.add_event_listener(self._handle_event)

    async def async_will_remove_from_hass(self) -> None:
        if self._unsubscribe_event:
            self._unsubscribe_event()
            self._unsubscribe_event = None
        if self._unsubscribe_connection:
            self._unsubscribe_connection()
            self._unsubscribe_connection = None
        await super().async_will_remove_from_hass()

    def _handle_connection_state(self, connected: bool) -> None:
        self._attr_available = connected
        if self.hass is not None:
            self.async_write_ha_state()

    def _handle_event(self, event: NormalizedEvent) -> None:
        """Override in subclasses to consume normalized events."""
