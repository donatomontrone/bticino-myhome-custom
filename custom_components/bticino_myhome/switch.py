"""Home Assistant switches backed by OpenWebNet WHO=3."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, WHO_LOAD_MANAGEMENT
from .entity import BticinoEntity
from .protocol import load_off, load_on


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    runtime = entry.runtime_data
    gateway = runtime.gateway
    manager = runtime.device_manager
    known = {d.key for d in manager.devices if d.device_type == "load"}

    initial = [
        BticinoLoadSwitch(gateway, d.who, d.where, d.name)
        for d in manager.devices
        if d.device_type == "load"
    ]
    async_add_entities(initial)

    def _device_added(device) -> None:
        if device.device_type != "load" or device.key in known:
            return
        known.add(device.key)
        async_add_entities([BticinoLoadSwitch(gateway, device.who, device.where, device.name)])

    entry.async_on_unload(manager.add_listener(_device_added))


class BticinoLoadSwitch(BticinoEntity, SwitchEntity):
    async def async_turn_on(self, **kwargs) -> None:
        await self.gateway.async_send(load_on(int(self.where)))

    async def async_turn_off(self, **kwargs) -> None:
        await self.gateway.async_send(load_off(int(self.where)))
