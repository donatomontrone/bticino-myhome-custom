"""Shared entity helpers."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .gateway import BticinoGateway


class BticinoEntity(Entity):
    """Base entity with local gateway availability and device metadata."""

    _gateway: BticinoGateway
    _unsubscribe_event = None
    _unsubscribe_connection = None

    def __init__(self, gateway: BticinoGateway, who: str, where: str, name: str) -> None:
        self._gateway = gateway
        self._who = who
        self._where = where
        self._attr_name = name or f"BTicino {who}/{where}"
        self._attr_available = gateway.connected

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._gateway.host}:{self._gateway.port}")},
            name="BTicino MyHome Gateway",
            manufacturer="BTicino / Legrand",
            model="OpenWebNet Gateway",
            configuration_url=f"http://{self._gateway.host}",
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._unsubscribe_connection = self._gateway.add_connection_listener(
            self._handle_connection_state
        )
        self._unsubscribe_event = self._gateway.add_listener(self._handle_raw_event)

    async def async_will_remove_from_hass(self) -> None:
        if self._unsubscribe_event:
            self._unsubscribe_event()
            self._unsubscribe_event = None
        if self._unsubscribe_connection:
            self._unsubscribe_connection()
            self._unsubscribe_connection = None
        await super().async_will_remove_from_hass()
        await super().async_will_remove_from_hass()

    def _handle_connection_state(self, connected: bool) -> None:
        self._attr_available = connected
        if self.hass is not None:
            self.async_write_ha_state()

    def _handle_raw_event(self, raw_message: str) -> None:
        """Override in subclasses."""
        return
