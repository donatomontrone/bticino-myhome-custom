"""Diagnostic sensor for raw WHO=7 events."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, WHO_VIDEO_DOOR_ENTRY
from .entity import BticinoEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    gateway = entry.runtime_data.gateway
    async_add_entities([BticinoIntercomEventLog(gateway, WHO_VIDEO_DOOR_ENTRY, "0", "Citofono - ultimo evento grezzo")])


class BticinoIntercomEventLog(BticinoEntity, SensorEntity):
    def __init__(self, gateway, who: str, where: str, name: str) -> None:
        BticinoEntity.__init__(self, gateway, who, where, name)
        self._attr_unique_id = f"{DOMAIN}_{who}_{where}_raw_event"
        self._attr_native_value = "nessun evento"

    def _handle_raw_event(self, raw_message: str) -> None:
        raw = raw_message.strip()
        if raw.startswith(f"*{WHO_VIDEO_DOOR_ENTRY}*"):
            self._attr_native_value = raw
            self.async_write_ha_state()
