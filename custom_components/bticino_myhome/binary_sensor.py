"""Video door-entry call indication (OpenWebNet WHO=7)."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    WHAT_VDE_CALL_END_1,
    WHAT_VDE_CALL_END_2,
    WHAT_VDE_CALL_START,
    WHO_VIDEO_DOOR_ENTRY,
)
from .data import BticinoConfigEntry
from .entity import BticinoEntity
from .gateway import BticinoGateway
from .platform import setup_dynamic_entities
from .protocol import NormalizedEvent


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BticinoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    gateway = entry.runtime_data.gateway
    setup_dynamic_entities(
        hass,
        entry,
        async_add_entities,
        matches=lambda device: device.device_type == "intercom",
        factory=lambda device: BticinoIntercomCallSensor(
            gateway, device.who, device.where, device.name
        ),
    )


class BticinoIntercomCallSensor(BticinoEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.SOUND
    _attr_translation_key = "intercom_call"

    def __init__(
        self, gateway: BticinoGateway, who: str, where: str, name: str
    ) -> None:
        super().__init__(gateway, who, where, name)
        self._attr_is_on = False

    def _handle_event(self, event: NormalizedEvent) -> None:
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
