"""BTicino MyHome scene entity."""
from __future__ import annotations

from homeassistant.components.scene import Scene
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import BticinoEntity
from .protocol import scene_activate


class BticinoScene(BticinoEntity, Scene):
    """Scene entity for scenario devices."""

    async def async_activate(self, **kwargs: Any) -> None:
        await scene_activate(self._gateway, self._device.who, self._device.address)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up scene from config entry."""
