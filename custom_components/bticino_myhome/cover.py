"""Home Assistant covers backed by OpenWebNet WHO=2."""
from __future__ import annotations

from typing import Any

from homeassistant.components.cover import CoverDeviceClass, CoverEntity, CoverEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import BticinoEntity
from .protocol import NormalizedEvent, cover_close, cover_open, cover_stop


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    runtime = entry.runtime_data
    gateway = runtime.gateway
    manager = runtime.device_manager
    known = {device.key for device in manager.devices if device.device_type == "cover"}
    async_add_entities(
        [
            BticinoCover(gateway, device.who, device.where, device.name)
            for device in manager.devices
            if device.device_type == "cover"
        ]
    )

    def _device_added(device) -> None:
        if device.device_type != "cover" or device.key in known:
            return
        known.add(device.key)
        async_add_entities([BticinoCover(gateway, device.who, device.where, device.name)])

    entry.async_on_unload(manager.add_listener(_device_added))


class BticinoCover(BticinoEntity, CoverEntity):
    _attr_device_class = CoverDeviceClass.SHUTTER
    _attr_supported_features = (
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
    )

    async def async_open_cover(self, **kwargs: Any) -> None:
        await self.gateway.async_send(cover_open(self.where))

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self.gateway.async_send(cover_close(self.where))

    async def async_stop_cover(self, **kwargs: Any) -> None:
        await self.gateway.async_send(cover_stop(self.where))

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
