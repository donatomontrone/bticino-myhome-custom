"""Shared dynamic entity lifecycle helpers."""
from __future__ import annotations

from collections.abc import Callable

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .data import BticinoConfigEntry
from .discovery import DiscoveredDevice


def remove_runtime_entity(hass: HomeAssistant, entity: Entity) -> None:
    """Remove a live entity and its entity-registry entry when present."""
    registry = er.async_get(hass)
    if (
        entity.entity_id is not None
        and registry.async_get(entity.entity_id) is not None
    ):
        registry.async_remove(entity.entity_id)
        return
    if entity.hass is None:
        return
    hass.async_create_task(
        entity.async_remove(force_remove=True),
        f"bticino_myhome-remove-{entity.unique_id or entity.entity_id or 'entity'}",
    )


def setup_dynamic_entities[EntityT: Entity](
    hass: HomeAssistant,
    entry: BticinoConfigEntry,
    async_add_entities: AddEntitiesCallback,
    *,
    matches: Callable[[DiscoveredDevice], bool],
    factory: Callable[[DiscoveredDevice], EntityT],
) -> None:
    """Expose inventory-backed entities and track explicit removals."""
    manager = entry.runtime_data.device_manager
    entities: dict[str, EntityT] = {}
    initial: list[EntityT] = []

    for device in manager.devices:
        if not matches(device):
            continue
        entity = factory(device)
        entities[device.key] = entity
        initial.append(entity)
    if initial:
        async_add_entities(initial)

    def _device_added(device: DiscoveredDevice) -> None:
        if not matches(device) or device.key in entities:
            return
        entity = factory(device)
        entities[device.key] = entity
        async_add_entities([entity])

    def _device_removed(device: DiscoveredDevice) -> None:
        entity = entities.pop(device.key, None)
        if entity is not None:
            remove_runtime_entity(hass, entity)

    entry.async_on_unload(manager.add_listener(_device_added))
    entry.async_on_unload(manager.add_remove_listener(_device_removed))
