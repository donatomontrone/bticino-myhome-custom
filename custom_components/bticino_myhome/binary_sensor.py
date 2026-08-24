"""Video door-entry call indication (OpenWebNet WHO=7)."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, WHAT_VDE_CALL_END_1, WHAT_VDE_CALL_END_2, WHAT_VDE_CALL_START, WHO_VIDEO_DOOR_ENTRY
from .entity import BticinoEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    gateway = entry.runtime_data.gateway
    devices = entry.runtime_data.devices
    entities = [
        BticinoIntercomCallSensor(gateway, d.who, d.where, d.name)
        for d in devices if d.device_type == "intercom"
    ]
    if not entities:
        entities.append(BticinoIntercomCallSensor(gateway, WHO_VIDEO_DOOR_ENTRY, "0", "Citofono / Hometouch - chiamata"))
    async_add_entities(entities)


class BticinoIntercomCallSensor(BticinoEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.SOUND

    def __init__(self, gateway, who: str, where: str, name: str) -> None:
        BticinoEntity.__init__(self, gateway, who, where, name)
        self._attr_unique_id = f"{DOMAIN}_{who}_{where}_intercom_call"
        self._attr_is_on = False

    def _handle_raw_event(self, raw_message: str) -> None:
        raw = raw_message.strip()
        if not raw.startswith(f"*{WHO_VIDEO_DOOR_ENTRY}*"):
            return
        if f"*{WHAT_VDE_CALL_START}*" in raw:
            self._attr_is_on = True
        elif f"*{WHAT_VDE_CALL_END_1}*" in raw or f"*{WHAT_VDE_CALL_END_2}*" in raw:
            self._attr_is_on = False
        else:
            return
        if self._where == "0" or f"*{self._where}##" in raw:
            self.async_write_ha_state()
