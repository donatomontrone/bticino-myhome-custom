"""Binary sensors for BTicino MyHome WHO=5 alarm state and diagnostics."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import WHO_ALARM
from .data import BticinoConfigEntry
from .discovery import DiscoveredDevice
from .entity import BticinoEntity
from .gateway import BticinoGateway, BticinoGatewayError
from .platform import remove_runtime_entity
from .protocol import (
    NormalizedEvent,
    alarm_partition_status_request,
    alarm_system_status_request,
)
from .protocol.alarm import (
    MAX_LEGACY_PARTITIONS,
    WHAT_BATTERY_FAULT,
    WHAT_BATTERY_OK,
    WHAT_BATTERY_UNLOADED,
    WHAT_NETWORK_FAULT,
    WHAT_NETWORK_OK,
    WHAT_TECHNICAL_ALARM,
    WHAT_TECHNICAL_ALARM_RESET,
    WHAT_ZONE_DISENGAGED,
    WHAT_ZONE_ENGAGED,
)

_LOGGER = logging.getLogger(__name__)
_MAX_TECHNICAL_ALARM_AUX = 9


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BticinoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Expose documented WHO=5 partition and diagnostic state surfaces."""
    gateway = entry.runtime_data.gateway
    manager = entry.runtime_data.device_manager
    groups: dict[str, list[BticinoEntity]] = {}

    def _build_group(device: DiscoveredDevice) -> list[BticinoEntity]:
        entities: list[BticinoEntity] = [
            BticinoAlarmPartitionSensor(gateway, device.where, device.name, partition)
            for partition in range(1, MAX_LEGACY_PARTITIONS + 1)
        ]
        entities.extend(
            [
                BticinoAlarmBatteryProblemSensor(gateway, device.where, device.name),
                BticinoAlarmNetworkConnectivitySensor(gateway, device.where, device.name),
            ]
        )
        entities.extend(
            BticinoAlarmTechnicalAlarmSensor(
                gateway, device.where, device.name, auxiliary
            )
            for auxiliary in range(1, _MAX_TECHNICAL_ALARM_AUX + 1)
        )
        return entities

    initial: list[BticinoEntity] = []
    for device in manager.devices:
        if device.device_type != "alarm":
            continue
        entities = _build_group(device)
        groups[device.key] = entities
        initial.extend(entities)
    if initial:
        async_add_entities(initial)

    def _device_added(device: DiscoveredDevice) -> None:
        if device.device_type != "alarm" or device.key in groups:
            return
        entities = _build_group(device)
        groups[device.key] = entities
        async_add_entities(entities)

    def _device_removed(device: DiscoveredDevice) -> None:
        for entity in groups.pop(device.key, []):
            remove_runtime_entity(hass, entity)

    entry.async_on_unload(manager.add_listener(_device_added))
    entry.async_on_unload(manager.add_remove_listener(_device_removed))


class BticinoAlarmPartitionSensor(BticinoEntity, BinarySensorEntity):
    """Active/partialized state for one documented WHO=5 central zone."""

    _request_initial_state_on_add = True
    _attr_translation_key = "alarm_partition"

    def __init__(
        self,
        gateway: BticinoGateway,
        alarm_where: str,
        alarm_name: str,
        partition: int,
    ) -> None:
        super().__init__(gateway, WHO_ALARM, alarm_where, alarm_name)
        self._partition = partition
        self._attr_translation_placeholders = {"partition": str(partition)}
        self._attr_unique_id = (
            f"{gateway.identity}:{WHO_ALARM}:{alarm_where}:partition:{partition}"
        )
        self._attr_is_on = None

    async def _async_request_initial_state(self) -> None:
        try:
            await self.gateway.async_send(
                alarm_partition_status_request(self._partition),
                is_status_request=True,
            )
        except BticinoGatewayError as err:
            _LOGGER.debug(
                "WHO=5 partition %s status request failed: %s",
                self._partition,
                err,
            )

    def _handle_event(self, event: NormalizedEvent) -> None:
        if event.who != WHO_ALARM or event.where != f"#{self._partition}":
            return
        if event.what == WHAT_ZONE_ENGAGED:
            self._attr_is_on = True
        elif event.what == WHAT_ZONE_DISENGAGED:
            self._attr_is_on = False
        else:
            return
        if self.hass is not None:
            self.async_write_ha_state()


class _BticinoAlarmCentralDiagnosticSensor(BticinoEntity, BinarySensorEntity):
    """Base for central WHO=5 diagnostics hydrated from the full alarm snapshot."""

    _request_initial_state_on_add = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    async def _async_request_initial_state(self) -> None:
        try:
            await self.gateway.async_send(
                alarm_system_status_request(), is_status_request=True
            )
        except BticinoGatewayError as err:
            _LOGGER.debug("WHO=5 diagnostic status request failed: %s", err)


class BticinoAlarmBatteryProblemSensor(_BticinoAlarmCentralDiagnosticSensor):
    """Documented 4200C/system battery fault state."""

    _attr_translation_key = "alarm_battery_problem"
    _attr_device_class = BinarySensorDeviceClass.BATTERY

    def __init__(
        self, gateway: BticinoGateway, alarm_where: str, alarm_name: str
    ) -> None:
        super().__init__(gateway, WHO_ALARM, alarm_where, alarm_name)
        self._attr_unique_id = (
            f"{gateway.identity}:{WHO_ALARM}:{alarm_where}:battery_problem"
        )
        self._attr_is_on = None

    def _handle_event(self, event: NormalizedEvent) -> None:
        if event.who != WHO_ALARM or event.where != "0":
            return
        if event.what in {WHAT_BATTERY_FAULT, WHAT_BATTERY_UNLOADED}:
            self._attr_is_on = True
        elif event.what == WHAT_BATTERY_OK:
            self._attr_is_on = False
        else:
            return
        if self.hass is not None:
            self.async_write_ha_state()


class BticinoAlarmNetworkConnectivitySensor(_BticinoAlarmCentralDiagnosticSensor):
    """Documented 4200C/system mains/network-present state."""

    _attr_translation_key = "alarm_network_connectivity"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(
        self, gateway: BticinoGateway, alarm_where: str, alarm_name: str
    ) -> None:
        super().__init__(gateway, WHO_ALARM, alarm_where, alarm_name)
        self._attr_unique_id = (
            f"{gateway.identity}:{WHO_ALARM}:{alarm_where}:network_connectivity"
        )
        self._attr_is_on = None

    def _handle_event(self, event: NormalizedEvent) -> None:
        if event.who != WHO_ALARM or event.where != "0":
            return
        if event.what == WHAT_NETWORK_OK:
            self._attr_is_on = True
        elif event.what == WHAT_NETWORK_FAULT:
            self._attr_is_on = False
        else:
            return
        if self.hass is not None:
            self.async_write_ha_state()


class BticinoAlarmTechnicalAlarmSensor(_BticinoAlarmCentralDiagnosticSensor):
    """Technical-alarm state for one documented WHO=5 auxiliary source."""

    _attr_translation_key = "alarm_technical_alarm"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        gateway: BticinoGateway,
        alarm_where: str,
        alarm_name: str,
        auxiliary: int,
    ) -> None:
        super().__init__(gateway, WHO_ALARM, alarm_where, alarm_name)
        self._auxiliary = auxiliary
        self._attr_translation_placeholders = {"auxiliary": str(auxiliary)}
        self._attr_unique_id = (
            f"{gateway.identity}:{WHO_ALARM}:{alarm_where}:technical_alarm:{auxiliary}"
        )
        self._attr_is_on = None

    def _handle_event(self, event: NormalizedEvent) -> None:
        if event.who != WHO_ALARM or event.where != f"#{self._auxiliary}":
            return
        if event.what == WHAT_TECHNICAL_ALARM:
            self._attr_is_on = True
        elif event.what == WHAT_TECHNICAL_ALARM_RESET:
            self._attr_is_on = False
        else:
            return
        if self.hass is not None:
            self.async_write_ha_state()
