"""Home Assistant covers backed by OpenWebNet WHO=2."""
from __future__ import annotations

from typing import Any

from homeassistant.components.cover import CoverDeviceClass, CoverEntity, CoverEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .data import BticinoConfigEntry
from .entity import BticinoEntity
from .platform import setup_dynamic_entities
from .protocol import NormalizedEvent, cover_close, cover_open, cover_stop


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BticinoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    gateway = entry.runtime_data.gateway
    setup_dynamic_entities(
        hass,
        entry,
        async_add_entities,
        matches=lambda device: device.device_type == "cover",
        factory=lambda device: BticinoCover(
            gateway, device.who, device.where, device.name
        ),
    )


class BticinoCover(BticinoEntity, CoverEntity):
    _attr_device_class = CoverDeviceClass.SHUTTER
    _attr_supported_features = (
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
    )
    _request_initial_state_on_add = True

    async def async_open_cover(self, **kwargs: Any) -> None:
        await self._async_send_command(cover_open(self.where))

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self._async_send_command(cover_close(self.where))

    async def async_stop_cover(self, **kwargs: Any) -> None:
        await self._async_send_command(cover_stop(self.where))

    def _handle_event(self, event: NormalizedEvent) -> None:
        if event.who != self.who or event.where != self.where:
            return
        if event.state == "opening":
            self._attr_is_opening = True
            self._attr_is_closing = False
        elif event.state == "closing":
            self._attr_is_opening = False
            self._attr_is_closing = True
        elif event.state == "stopped":
            self._attr_is_opening = False
            self._attr_is_closing = False
        else:
            return
        if self.hass is not None:
            self.async_write_ha_state()
