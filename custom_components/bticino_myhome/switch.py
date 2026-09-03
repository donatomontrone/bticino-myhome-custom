"""BTicino MyHome switch entity."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import BticinoEntity
from .protocol import load_off, load_on


class BticinoSwitch(BticinoEntity, SwitchEntity):
    """Switch entity for load management devices."""

    async def async_turn_on(self, **kwargs: Any) -> None:
        await load_on(self._gateway, self._device.who, self._device.address)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await load_off(self._gateway, self._device.who, self._device.address)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch from config entry."""
