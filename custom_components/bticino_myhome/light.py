"""Home Assistant lights backed by OpenWebNet WHO=1."""
from __future__ import annotations

from homeassistant.components.light import LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, WHO_LIGHTING
from .protocol import light_off, light_on
from .entity import BticinoEntity


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
    _attr_icon = "mdi:lightbulb"

    def __init__(self, gateway, who: str, where: str, name: str) -> None:
        BticinoEntity.__init__(self, gateway, who, where, name)
        self._attr_unique_id = f"{DOMAIN}_{who}_{where}_light"
        self._attr_is_on = False

    async def async_turn_on(self, **kwargs) -> None:
        await self._gateway.async_send(light_on(self._where))

    async def async_turn_off(self, **kwargs) -> None:
        await self._gateway.async_send(light_off(self._where))

    def _handle_event(self, event) -> None:
        if event.who != WHO_LIGHTING or event.where != self._where:
            return
        if event.state == "on":
            self._attr_is_on = True
            self.async_write_ha_state()
        elif event.state == "off":
            self._attr_is_on = False
            self.async_write_ha_state()
