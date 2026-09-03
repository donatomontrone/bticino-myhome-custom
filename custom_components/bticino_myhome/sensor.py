"""Diagnostic sensors for BTicino MyHome."""
from __future__ import annotations

from collections.abc import Callable

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, WHO_VIDEO_DOOR_ENTRY
from .gateway import BticinoGateway
from .protocol import NormalizedEvent


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    gateway = entry.runtime_data.gateway
    manager = entry.runtime_data.device_manager
    created = any(device.who == WHO_VIDEO_DOOR_ENTRY for device in manager.devices)
    if created:
        async_add_entities([BticinoIntercomEventLog(gateway)])

    def _device_added(device) -> None:
        nonlocal created
        if created or device.who != WHO_VIDEO_DOOR_ENTRY:
            return
        created = True
        async_add_entities([BticinoIntercomEventLog(gateway)])

    entry.async_on_unload(manager.add_listener(_device_added))


class BticinoIntercomEventLog(SensorEntity):
    """Disabled-by-default gateway diagnostic for the last WHO=7 frame."""

    _attr_should_poll = False
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_name = "Video door entry - last raw event"

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
