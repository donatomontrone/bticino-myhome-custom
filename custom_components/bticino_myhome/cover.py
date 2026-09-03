"""BTicino MyHome cover entity."""
from __future__ import annotations

from homeassistant.components.cover import CoverEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import BticinoEntity
from .protocol import build_status_request, cover_close, cover_open, cover_stop


class BticinoCover(BticinoEntity, CoverEntity):
    """Cover entity for automation devices."""

    async def async_added_to_hass(self) -> None:
        """Request initial state from the bus when entity is added."""
        await super().async_added_to_hass()
        # Send status request to populate real state instead of optimistic None
        await self._gateway.async_send(
            build_status_request(self._device.who, self._device.address)
        )

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
