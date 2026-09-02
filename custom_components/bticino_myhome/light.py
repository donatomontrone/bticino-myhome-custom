"""Home Assistant lights backed by OpenWebNet WHO=1."""
from __future__ import annotations

from homeassistant.components.light import LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, WHO_LIGHTING
from .entity import BticinoEntity
from .protocol import light_off, light_on


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    runtime = entry.runtime_data
    gateway = runtime.gateway
    manager = runtime.device_manager
    known = {d.key for d in manager.devices if d.device_type == "light"}

    initial = [
        BticinoLight(gateway, d.who, d.where, d.name)
        for d in manager.devices
        if d.device_type == "light"
    ]
    async_add_entities(initial)

    def _device_added(device) -> None:
        if device.device_type != "light" or device.key in known:
            return
        known.add(device.key)
        async_add_entities([BticinoLight(gateway, device.who, device.where, device.name)])

    entry.async_on_unload(manager.add_listener(_device_added))


class BticinoLight(BticinoEntity, LightEntity):
    async def async_turn_on(self, **kwargs) -> None:
        await self.gateway.async_send(light_on(int(self.where)))

    async def async_turn_off(self, **kwargs) -> None:
        await self.gateway.async_send(light_off(int(self.where)))
