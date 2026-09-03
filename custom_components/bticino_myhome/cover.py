"""BTicino MyHome cover entity."""
from __future__ import annotations

from homeassistant.components.cover import CoverEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import BticinoEntity
from .protocol import cover_close, cover_open, cover_stop


class BticinoCover(BticinoEntity, CoverEntity):
    """Cover entity for automation devices."""

    async def async_open_cover(self) -> None:
        await cover_open(self._gateway, self._device.who, self._device.address)

    async def async_close_cover(self) -> None:
        await cover_close(self._gateway, self._device.who, self._device.address)

    async def async_stop_cover(self) -> None:
        await cover_stop(self._gateway, self._device.who, self._device.address)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up cover from config entry."""
