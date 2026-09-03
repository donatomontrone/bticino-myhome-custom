"""Home Assistant lights backed by OpenWebNet WHO=1."""
from __future__ import annotations

from typing import Any

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .data import BticinoConfigEntry
from .entity import BticinoEntity
from .gateway import BticinoGateway
from .platform import setup_dynamic_entities
from .protocol import NormalizedEvent, light_off, light_on


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
        matches=lambda device: device.device_type == "light",
        factory=lambda device: BticinoLight(
            gateway, device.who, device.where, device.name
        ),
    )


class BticinoLight(BticinoEntity, LightEntity):
    _attr_color_mode = ColorMode.ONOFF
    _request_initial_state_on_add = True

    def __init__(
        self, gateway: BticinoGateway, who: str, where: str, name: str
    ) -> None:
        super().__init__(gateway, who, where, name)
        self._attr_supported_color_modes = {ColorMode.ONOFF}

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.gateway.async_send(light_on(self.where))

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.gateway.async_send(light_off(self.where))

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
