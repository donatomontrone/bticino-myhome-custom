"""Binary sensors for BTicino MyHome alarm partitions."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import WHO_ALARM
from .data import BticinoConfigEntry
from .discovery import DiscoveredDevice
from .entity import BticinoEntity
from .gateway import BticinoGateway, BticinoGatewayError
from .platform import remove_runtime_entity
from .protocol import NormalizedEvent, alarm_partition_status_request
from .protocol.alarm import (
    MAX_LEGACY_PARTITIONS,
    WHAT_ZONE_DISENGAGED,
    WHAT_ZONE_ENGAGED,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BticinoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Expose the documented WHO=5 central-zone/partition state surface."""
    gateway = entry.runtime_data.gateway
    manager = entry.runtime_data.device_manager
    groups: dict[str, list[BticinoAlarmPartitionSensor]] = {}

    def _build_group(device: DiscoveredDevice) -> list[BticinoAlarmPartitionSensor]:
        return [
            BticinoAlarmPartitionSensor(gateway, device.where, device.name, partition)
            for partition in range(1, MAX_LEGACY_PARTITIONS + 1)
        ]

    initial: list[BticinoAlarmPartitionSensor] = []
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
    _attr_name: str | None = None

    def __init__(
        self,
        gateway: BticinoGateway,
        alarm_where: str,
        alarm_name: str,
        partition: int,
    ) -> None:
        super().__init__(gateway, WHO_ALARM, alarm_where, alarm_name)
        self._partition = partition
        self._attr_name = f"Partition {partition}"
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
