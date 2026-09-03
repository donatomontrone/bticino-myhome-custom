"""Video door-entry call indication (OpenWebNet WHO=7)."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import WHAT_VDE_CALL_END_1, WHAT_VDE_CALL_END_2, WHAT_VDE_CALL_START, WHO_VIDEO_DOOR_ENTRY
from .entity import BticinoEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    gateway = entry.runtime_data.gateway
    manager = entry.runtime_data.device_manager
    devices = [device for device in manager.devices if device.device_type == "intercom"]
    known = {device.key for device in devices}
    if devices:
        async_add_entities(
            [
                BticinoIntercomCallSensor(gateway, device.who, device.where, device.name)
                for device in devices
            ]
        )

    def _device_added(device) -> None:
        if device.device_type != "intercom" or device.key in known:
            return
        known.add(device.key)
        async_add_entities(
            [BticinoIntercomCallSensor(gateway, device.who, device.where, device.name)]
        )

    entry.async_on_unload(manager.add_listener(_device_added))


class BticinoIntercomCallSensor(BticinoEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.SOUND

    def __init__(self, gateway, who: str, where: str, name: str) -> None:
        BticinoEntity.__init__(self, gateway, who, where, name)
        self._attr_is_on = False

    def _handle_event(self, event) -> None:
        if event.who != WHO_VIDEO_DOOR_ENTRY or event.where != self.where:
            return
        if event.what == WHAT_VDE_CALL_START:
            self._attr_is_on = True
        elif event.what in (WHAT_VDE_CALL_END_1, WHAT_VDE_CALL_END_2):
            self._attr_is_on = False
        else:
            return
        if self.hass is not None:
            self.async_write_ha_state()
