"""BTicino MyHome light entity."""
from __future__ import annotations

from typing import ClassVar

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import BticinoEntity
from .protocol import light_off, light_on


class BticinoLight(BticinoEntity, LightEntity):
    """Light entity for lighting devices."""

    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes: ClassVar[set[ColorMode]] = {ColorMode.ONOFF}

    async def async_turn_on(self, **kwargs: Any) -> None:
        await light_on(self._gateway, self._device.who, self._device.address)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await light_off(self._gateway, self._device.who, self._device.address)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up light from config entry."""
