"""Door-lock release button via OpenWebNet WHO=7."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, WHAT_VDE_LOCK_RELEASE, WHO_VIDEO_DOOR_ENTRY
from .entity import BticinoEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    gateway = entry.runtime_data.gateway
    async_add_entities([BticinoDoorLockButton(gateway, WHO_VIDEO_DOOR_ENTRY, "0", "Apri serratura ingresso")])


class BticinoDoorLockButton(BticinoEntity, ButtonEntity):
    _attr_icon = "mdi:lock-open-variant"

    def __init__(self, gateway, who: str, where: str, name: str) -> None:
        BticinoEntity.__init__(self, gateway, who, where, name)
        self._attr_unique_id = f"{DOMAIN}_{who}_{where}_door_lock"

    async def async_press(self) -> None:
        await self._gateway.async_send(f"*{WHO_VIDEO_DOOR_ENTRY}*{WHAT_VDE_LOCK_RELEASE}*{self._where}##")
