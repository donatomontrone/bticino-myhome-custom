"""Home Assistant switches backed by OpenWebNet WHO=3."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, WHO_LOAD_MANAGEMENT
from .entity import BticinoEntity


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
    def __init__(self, gateway, who: str, where: str, name: str) -> None:
        BticinoEntity.__init__(self, gateway, who, where, name)
        self._attr_unique_id = f"{DOMAIN}_{who}_{where}_load"
        self._attr_is_on = False

    async def async_turn_on(self, **kwargs) -> None:
        await self._gateway.async_send(f"*{WHO_LOAD_MANAGEMENT}*1*{self._where}##")

    async def async_turn_off(self, **kwargs) -> None:
        await self._gateway.async_send(f"*{WHO_LOAD_MANAGEMENT}*0*{self._where}##")

    def _handle_raw_event(self, raw_message: str) -> None:
        raw = raw_message.strip()
        if raw == f"*{WHO_LOAD_MANAGEMENT}*1*{self._where}##":
            self._attr_is_on = True
            self.async_write_ha_state()
        elif raw == f"*{WHO_LOAD_MANAGEMENT}*0*{self._where}##":
            self._attr_is_on = False
            self.async_write_ha_state()
