"""OpenWebNet scenario activation (WHO=0)."""
from __future__ import annotations

from homeassistant.components.scene import Scene
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import BticinoEntity
from .protocol import scene_activate


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    runtime = entry.runtime_data
    gateway = runtime.gateway
    manager = runtime.device_manager
    known = {d.key for d in manager.devices if d.device_type == "scene"}

    initial = [
        BticinoScene(gateway, d.who, d.where, d.name)
        for d in manager.devices
        if d.device_type == "scene"
    ]
    async_add_entities(initial)

    def _device_added(device) -> None:
        if device.device_type != "scene" or device.key in known:
            return
        known.add(device.key)
        async_add_entities([BticinoScene(gateway, device.who, device.where, device.name)])

    entry.async_on_unload(manager.add_listener(_device_added))


class BticinoScene(BticinoEntity, Scene):
    async def async_activate(self, **kwargs) -> None:
        await self.gateway.async_send(scene_activate(int(self.where)))
