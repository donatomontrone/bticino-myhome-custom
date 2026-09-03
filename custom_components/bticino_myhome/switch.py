"""Home Assistant switches backed by OpenWebNet WHO=3."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .data import BticinoConfigEntry
from .entity import BticinoEntity
from .platform import setup_dynamic_entities
from .protocol import NormalizedEvent, load_off, load_on


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
        matches=lambda device: device.device_type == "load",
        factory=lambda device: BticinoLoadSwitch(
            gateway, device.who, device.where, device.name
        ),
    )


class BticinoLoadSwitch(BticinoEntity, SwitchEntity):
    _request_initial_state_on_add = True

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.gateway.async_send(load_on(self.where))

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.gateway.async_send(load_off(self.where))

    def _handle_event(self, event: NormalizedEvent) -> None:
        if event.who != self.who or event.where != self.where:
            return
        if event.state == "on":
            self._attr_is_on = True
        elif event.state == "off":
            self._attr_is_on = False
        else:
            return
        if self.hass is not None:
            self.async_write_ha_state()
