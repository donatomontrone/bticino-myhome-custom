"""OpenWebNet scenario activation (WHO=0)."""
from __future__ import annotations

from homeassistant.components.scene import Scene
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, WHO_SCENARIO
from .protocol import scene_activate
from .entity import BticinoEntity


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
    def __init__(self, gateway, who: str, where: str, name: str) -> None:
        BticinoEntity.__init__(self, gateway, who, where, name)
        self._attr_unique_id = f"{DOMAIN}_{who}_{where}_scene"

    async def async_activate(self, **kwargs) -> None:
        await self._gateway.async_send(scene_activate(self._where))
