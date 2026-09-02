"""OpenWebNet scenario activation (WHO=0)."""
from __future__ import annotations

from homeassistant.components.scene import Scene
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, WHO_SCENARIO
from .entity import BticinoEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    gateway = entry.runtime_data.gateway
    devices = entry.runtime_data.device_manager.devices
    async_add_entities(
        [BticinoScene(gateway, d.who, d.where, d.name) for d in devices if d.device_type == "scene"]
    )


class BticinoScene(BticinoEntity, Scene):
    def __init__(self, gateway, who: str, where: str, name: str) -> None:
        BticinoEntity.__init__(self, gateway, who, where, name)
        self._attr_unique_id = f"{DOMAIN}_{who}_{where}_scene"

    async def async_activate(self, **kwargs) -> None:
        await self._gateway.async_send(f"*{WHO_SCENARIO}*1*{self._where}##")
