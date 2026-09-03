"""BTicino MyHome button entity."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import BticinoEntity
from .protocol import door_lock_release


class BticinoButton(BticinoEntity, ButtonEntity):
    """Button entity for video door entry lock release."""

    async def async_press(self) -> None:
        await door_lock_release(self._gateway, self._device.who, self._device.address)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button from config entry."""
