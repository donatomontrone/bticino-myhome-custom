"""Home Assistant covers backed by OpenWebNet WHO=2."""
from __future__ import annotations

from homeassistant.components.cover import CoverDeviceClass, CoverEntity, CoverEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, WHO_AUTOMATION
from .protocol import cover_close, cover_open, cover_stop
from .entity import BticinoEntity


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
    _attr_supported_features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP

    def __init__(self, gateway, who: str, where: str, name: str) -> None:
        BticinoEntity.__init__(self, gateway, who, where, name)
        self._attr_unique_id = f"{DOMAIN}_{who}_{where}_cover"
        self._attr_is_closed = None

    async def async_open_cover(self, **kwargs) -> None:
        await self._gateway.async_send(cover_open(self._where))

    async def async_close_cover(self, **kwargs) -> None:
        await self._gateway.async_send(cover_close(self._where))

    async def async_stop_cover(self, **kwargs) -> None:
        await self._gateway.async_send(cover_stop(self._where))

    def _handle_event(self, event) -> None:
        if event.who != WHO_AUTOMATION or event.where != self._where:
            return
        if event.state == "open":
            self._attr_is_closed = False
            self.async_write_ha_state()
        elif event.state == "closed":
            self._attr_is_closed = True
            self.async_write_ha_state()
