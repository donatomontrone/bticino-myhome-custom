"""OpenWebNet scenario activation (WHO=0)."""
from __future__ import annotations

from typing import Any

from homeassistant.components.scene import Scene
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .data import BticinoConfigEntry
from .entity import BticinoEntity
from .platform import setup_dynamic_entities
from .protocol import scene_activate


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
        matches=lambda device: device.device_type == "scene",
        factory=lambda device: BticinoScene(
            gateway, device.who, device.where, device.name
        ),
    )


class BticinoScene(BticinoEntity, Scene):
    async def async_activate(self, **kwargs: Any) -> None:
        await self.gateway.async_send(scene_activate(self.where))
