"""Home Assistant switches backed by OpenWebNet WHO=3."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import BticinoEntity
from .protocol import NormalizedEvent, load_off, load_on


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    runtime = entry.runtime_data
    gateway = runtime.gateway
    manager = runtime.device_manager
    known = {device.key for device in manager.devices if device.device_type == "load"}
    async_add_entities(
        [
            BticinoLoadSwitch(gateway, device.who, device.where, device.name)
            for device in manager.devices
            if device.device_type == "load"
        ]
    )

    def _device_added(device) -> None:
        if device.device_type != "load" or device.key in known:
            return
        known.add(device.key)
        async_add_entities([BticinoLoadSwitch(gateway, device.who, device.where, device.name)])

    entry.async_on_unload(manager.add_listener(_device_added))


class BticinoLoadSwitch(BticinoEntity, SwitchEntity):
    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.gateway.async_send(load_on(self.where))

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.gateway.async_send(load_off(self.where))

    def _handle_event(self, event: NormalizedEvent) -> None:
        if event.who != self.who or event.where != self.where:
            return
        if event.state == "on":
            self._attr_is_on = True
        elif event.state == "off":
            self._attr_is_on = False
        else:
            return
        if self.hass is not None:
            self.async_write_ha_state()
