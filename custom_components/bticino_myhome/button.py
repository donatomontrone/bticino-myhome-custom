"""Door-lock release button via OpenWebNet WHO=7."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, WHO_VIDEO_DOOR_ENTRY
from .entity import BticinoEntity
from .protocol import door_lock_release


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    runtime = entry.runtime_data
    gateway = runtime.gateway
    manager = runtime.device_manager
    known = {d.key for d in manager.devices if d.device_type == "door_lock"}

    initial = [
        BticinoDoorLockRelease(gateway, d.who, d.where, d.name)
        for d in manager.devices
        if d.device_type == "door_lock"
    ]
    async_add_entities(initial)

    def _device_added(device) -> None:
        if device.device_type != "door_lock" or device.key in known:
            return
        known.add(device.key)
        async_add_entities([BticinoDoorLockRelease(gateway, device.who, device.where, device.name)])

    entry.async_on_unload(manager.add_listener(_device_added))


class BticinoDoorLockRelease(BticinoEntity, ButtonEntity):
    async def async_press(self) -> None:
        await self.gateway.async_send(door_lock_release(int(self.where)))
