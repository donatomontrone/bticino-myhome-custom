"""Sensors for BTicino MyHome."""
from __future__ import annotations

import logging
from collections.abc import Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, WHO_VIDEO_DOOR_ENTRY
from .data import BticinoConfigEntry
from .discovery import DiscoveredDevice
from .entity import BticinoEntity
from .gateway import BticinoGateway, BticinoGatewayError
from .platform import remove_runtime_entity, setup_dynamic_entities
from .protocol import NormalizedEvent, build_dimension_request
from .protocol.energy import (
    DIM_ACTIVE_POWER,
    WHO_ENERGY_MANAGEMENT,
    decode_active_power,
    is_energy_meter_where,
)

_LOGGER = logging.getLogger(__name__)


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
        matches=lambda device: (
            device.device_type == "energy" and is_energy_meter_where(device.where)
        ),
        factory=lambda device: BticinoActivePowerSensor(
            gateway, device.who, device.where, device.name
        ),
    )

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


class BticinoActivePowerSensor(BticinoEntity, SensorEntity):
    """Read-only active-power measurement for a documented WHO=18 5N meter."""

    _attr_translation_key = "active_power"
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _request_initial_state_on_add = True

    async def _async_request_initial_state(self) -> None:
        try:
            await self.gateway.async_send(
                build_dimension_request(
                    WHO_ENERGY_MANAGEMENT, self.where, DIM_ACTIVE_POWER
                ),
                is_status_request=True,
            )
        except BticinoGatewayError as err:
            _LOGGER.debug(
                "WHO=18 active-power request failed for WHERE=%s: %s",
                self.where,
                err,
            )

    def _handle_event(self, event: NormalizedEvent) -> None:
        if (
            event.who != self.who
            or event.where != self.where
            or event.dimension != DIM_ACTIVE_POWER
        ):
            return
        power = decode_active_power(event.values)
        if power is None:
            return
        self._attr_native_value = power
        if self.hass is not None:
            self.async_write_ha_state()


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
