"""Shared entity helpers."""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, cast

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .gateway import BticinoGateway, BticinoGatewayError
from .protocol import NormalizedEvent, build_status_request

_LOGGER = logging.getLogger(__name__)


class BticinoEntity(Entity):
    _attr_should_poll = False
    _request_initial_state_on_add = False

    def __init__(self, gateway: BticinoGateway, who: str, where: str, name: str) -> None:
        self._gateway = gateway
        self._who = str(who)
        self._where = str(where)
        self._attr_name = name or f"BTicino {who}/{where}"
        self._attr_unique_id = f"{gateway.identity}:{self._who}:{self._where}"
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
        info: dict[str, Any] = {
            "identifiers": {(DOMAIN, f"{self._gateway.identity}:{self._who}:{self._where}")},
            "name": self._attr_name,
            "manufacturer": "BTicino / Legrand",
            "model": f"MyHome OpenWebNet WHO={self._who}",
        }
        if self.hass is not None:
            hub = dr.async_get(self.hass).async_get_device(
                identifiers={(DOMAIN, self._gateway.identity)}
            )
            if hub is not None:
                if "via_device_id" in DeviceInfo.__annotations__:
                    info["via_device_id"] = hub.id
                else:
                    info["via_device"] = (DOMAIN, self._gateway.identity)
        return cast(DeviceInfo, info)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._unsubscribe_connection = self._gateway.add_connection_listener(
            self._handle_connection_state
        )
        self._unsubscribe_event = self._gateway.add_event_listener(self._handle_event)
        if self._request_initial_state_on_add and self.hass is not None:
            task = self.hass.async_create_task(
                self._async_request_initial_state(),
                f"bticino_myhome-initial-state-{self._who}-{self._where}",
            )
            self.async_on_remove(task.cancel)

    async def async_will_remove_from_hass(self) -> None:
        if self._unsubscribe_event:
            self._unsubscribe_event()
            self._unsubscribe_event = None
        if self._unsubscribe_connection:
            self._unsubscribe_connection()
            self._unsubscribe_connection = None
        await super().async_will_remove_from_hass()

    async def _async_request_initial_state(self) -> None:
        """Request a state snapshot without inventing a local state."""
        try:
            await self._gateway.async_send(
                build_status_request(self._who, self._where),
                is_status_request=True,
            )
        except BticinoGatewayError as err:
            _LOGGER.debug(
                "Initial state request failed for WHO=%s WHERE=%s: %s",
                self._who,
                self._where,
                err,
            )

    def _handle_connection_state(self, connected: bool) -> None:
        self._attr_available = connected
        if self.hass is not None:
            self.async_write_ha_state()

    def _handle_event(self, event: NormalizedEvent) -> None:
        """Override in subclasses to consume normalized events."""
