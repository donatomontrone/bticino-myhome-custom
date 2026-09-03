"""Diagnostic sensors for BTicino MyHome."""
from __future__ import annotations

from collections.abc import Callable

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, WHO_VIDEO_DOOR_ENTRY
from .data import BticinoConfigEntry
from .discovery import DiscoveredDevice
from .gateway import BticinoGateway
from .platform import remove_runtime_entity
from .protocol import NormalizedEvent


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BticinoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    gateway = entry.runtime_data.gateway
    manager = entry.runtime_data.device_manager
    entity: BticinoIntercomEventLog | None = None

    def _ensure_entity() -> None:
        nonlocal entity
        if entity is not None:
            return
        entity = BticinoIntercomEventLog(gateway)
        async_add_entities([entity])

    if any(device.who == WHO_VIDEO_DOOR_ENTRY for device in manager.devices):
        _ensure_entity()

    def _device_added(device: DiscoveredDevice) -> None:
        if device.who == WHO_VIDEO_DOOR_ENTRY:
            _ensure_entity()

    def _device_removed(device: DiscoveredDevice) -> None:
        nonlocal entity
        if device.who != WHO_VIDEO_DOOR_ENTRY or entity is None:
            return
        if any(item.who == WHO_VIDEO_DOOR_ENTRY for item in manager.devices):
            return
        remove_runtime_entity(hass, entity)
        entity = None

    entry.async_on_unload(manager.add_listener(_device_added))
    entry.async_on_unload(manager.add_remove_listener(_device_removed))


class BticinoIntercomEventLog(SensorEntity):
    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_translation_key = "who7_raw_event"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(self, gateway: BticinoGateway) -> None:
        self._gateway = gateway
        self._attr_unique_id = f"{gateway.identity}:who7_raw_event"
        self._attr_native_value = None
        self._unsubscribe_event: Callable[[], None] | None = None

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self._gateway.identity)})

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._unsubscribe_event = self._gateway.add_event_listener(self._handle_event)

    async def async_will_remove_from_hass(self) -> None:
        if self._unsubscribe_event is not None:
            self._unsubscribe_event()
            self._unsubscribe_event = None
        await super().async_will_remove_from_hass()

    def _handle_event(self, event: NormalizedEvent) -> None:
        if event.who != WHO_VIDEO_DOOR_ENTRY:
            return
        self._attr_native_value = event.raw
        if self.hass is not None:
            self.async_write_ha_state()
