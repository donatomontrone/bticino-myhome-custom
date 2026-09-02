"""Home Assistant covers backed by OpenWebNet WHO=2."""
from __future__ import annotations

from homeassistant.components.cover import CoverDeviceClass, CoverEntity, CoverEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, WHO_AUTOMATION
from .entity import BticinoEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    gateway = entry.runtime_data.gateway
    devices = entry.runtime_data.device_manager.devices
    async_add_entities(
        [BticinoCover(gateway, d.who, d.where, d.name) for d in devices if d.device_type == "cover"]
    )


class BticinoCover(BticinoEntity, CoverEntity):
    _attr_device_class = CoverDeviceClass.SHUTTER
    _attr_supported_features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP

    def __init__(self, gateway, who: str, where: str, name: str) -> None:
        BticinoEntity.__init__(self, gateway, who, where, name)
        self._attr_unique_id = f"{DOMAIN}_{who}_{where}_cover"
        self._attr_is_closed = None

    async def async_open_cover(self, **kwargs) -> None:
        await self._gateway.async_send(f"*{WHO_AUTOMATION}*1*{self._where}##")

    async def async_close_cover(self, **kwargs) -> None:
        await self._gateway.async_send(f"*{WHO_AUTOMATION}*2*{self._where}##")

    async def async_stop_cover(self, **kwargs) -> None:
        await self._gateway.async_send(f"*{WHO_AUTOMATION}*0*{self._where}##")

    def _handle_raw_event(self, raw_message: str) -> None:
        raw = raw_message.strip()
        if raw == f"*{WHO_AUTOMATION}*1*{self._where}##":
            self._attr_is_closed = False
            self.async_write_ha_state()
        elif raw == f"*{WHO_AUTOMATION}*2*{self._where}##":
            self._attr_is_closed = True
            self.async_write_ha_state()
