"""Home Assistant covers backed by OpenWebNet WHO=2."""
from __future__ import annotations

from homeassistant.components.cover import CoverDeviceClass, CoverEntity, CoverEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, WHO_AUTOMATION
from .entity import BticinoEntity
from .protocol import cover_close, cover_open, cover_stop


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    runtime = entry.runtime_data
    gateway = runtime.gateway
    manager = runtime.device_manager
    known = {d.key for d in manager.devices if d.device_type == "cover"}

    initial = [
        BticinoCover(gateway, d.who, d.where, d.name)
        for d in manager.devices
        if d.device_type == "cover"
    ]
    async_add_entities(initial)

    def _device_added(device) -> None:
        if device.device_type != "cover" or device.key in known:
            return
        known.add(device.key)
        async_add_entities([BticinoCover(gateway, device.who, device.where, device.name)])

    entry.async_on_unload(manager.add_listener(_device_added))


class BticinoCover(BticinoEntity, CoverEntity):
    _attr_device_class = CoverDeviceClass.SHUTTER
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
    )

    async def async_open_cover(self, **kwargs) -> None:
        await self.gateway.async_send(cover_open(int(self.where)))

    async def async_close_cover(self, **kwargs) -> None:
        await self.gateway.async_send(cover_close(int(self.where)))

    async def async_stop_cover(self, **kwargs) -> None:
        await self.gateway.async_send(cover_stop(int(self.where)))
