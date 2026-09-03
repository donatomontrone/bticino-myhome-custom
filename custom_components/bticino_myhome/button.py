"""Reference-backed door-release button via OpenWebNet WHO=6."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .data import BticinoConfigEntry
from .entity import BticinoEntity
from .platform import setup_dynamic_entities
from .protocol import door_lock_release


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
        matches=lambda device: device.device_type in {"door_lock", "intercom"},
        factory=lambda device: BticinoDoorLockRelease(
            gateway, device.who, device.where, device.name
        ),
    )


class BticinoDoorLockRelease(BticinoEntity, ButtonEntity):
    _attr_translation_key = "door_release"

    async def async_press(self) -> None:
        await self._async_send_command(door_lock_release(self.where))
