"""Home Assistant lights backed by OpenWebNet WHO=1."""
from __future__ import annotations

from homeassistant.components.light import LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, WHO_LIGHTING
from .entity import BticinoEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    gateway = entry.runtime_data.gateway
    devices = entry.runtime_data.devices
    async_add_entities(
        [BticinoLight(gateway, d.who, d.where, d.name) for d in devices if d.device_type == "light"]
    )


class BticinoLight(BticinoEntity, LightEntity):
    _attr_icon = "mdi:lightbulb"

    def __init__(self, gateway, who: str, where: str, name: str) -> None:
        BticinoEntity.__init__(self, gateway, who, where, name)
        self._attr_unique_id = f"{DOMAIN}_{who}_{where}_light"
        self._attr_is_on = False

    async def async_turn_on(self, **kwargs) -> None:
        await self._gateway.async_send(f"*{WHO_LIGHTING}*1*{self._where}##")

    async def async_turn_off(self, **kwargs) -> None:
        await self._gateway.async_send(f"*{WHO_LIGHTING}*0*{self._where}##")

    def _handle_raw_event(self, raw_message: str) -> None:
        raw = raw_message.strip()
        if raw == f"*{WHO_LIGHTING}*1*{self._where}##":
            self._attr_is_on = True
            self.async_write_ha_state()
        elif raw == f"*{WHO_LIGHTING}*0*{self._where}##":
            self._attr_is_on = False
            self.async_write_ha_state()
