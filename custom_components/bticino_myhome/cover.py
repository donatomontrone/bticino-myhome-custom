"""Home Assistant covers backed by OpenWebNet WHO=2."""
from __future__ import annotations

from typing import Any

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .data import BticinoConfigEntry
from .entity import BticinoEntity
from .gateway import BticinoGateway, BticinoGatewayError
from .platform import setup_dynamic_entities
from .protocol import (
    NormalizedEvent,
    build_dimension_request,
    cover_close,
    cover_open,
    cover_stop,
)
from .protocol.automation import (
    CAPABILITY_POSITION_CONTROL,
    DIM_SHUTTER_STATUS,
    build_go_to_level,
    decode_shutter_status,
)

_BASE_FEATURES = (
    CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
)


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
        matches=lambda device: device.device_type == "cover",
        factory=lambda device: BticinoCover(
            gateway,
            device.who,
            device.where,
            device.name,
            capabilities=device.capabilities,
        ),
    )


class BticinoCover(BticinoEntity, CoverEntity):
    _attr_device_class = CoverDeviceClass.SHUTTER
    _request_initial_state_on_add = True

    def __init__(
        self,
        gateway: BticinoGateway,
        who: str,
        where: str,
        name: str,
        *,
        capabilities: tuple[str, ...] = (),
    ) -> None:
        super().__init__(gateway, who, where, name)
        self._supports_position = CAPABILITY_POSITION_CONTROL in capabilities
        self._attr_supported_features = _BASE_FEATURES
        if self._supports_position:
            self._attr_supported_features |= CoverEntityFeature.SET_POSITION
        self._attr_current_cover_position = None
        self._attr_is_opening = None
        self._attr_is_closing = None
        self._attr_is_closed = None

    async def _async_request_initial_state(self) -> None:
        await super()._async_request_initial_state()
        if not self._supports_position:
            return
        try:
            await self.gateway.async_send(
                build_dimension_request("2", self.where, DIM_SHUTTER_STATUS),
                is_status_request=True,
            )
        except BticinoGatewayError:
            # The generic WHO=2 status request may still have hydrated motion
            # state; absence of DIM=10 must not fabricate or clear position.
            return

    async def async_open_cover(self, **kwargs: Any) -> None:
        await self._async_send_command(cover_open(self.where))

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self._async_send_command(cover_close(self.where))

    async def async_stop_cover(self, **kwargs: Any) -> None:
        await self._async_send_command(cover_stop(self.where))

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        if not self._supports_position:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="cover_position_not_supported",
            )
        position = int(kwargs[ATTR_POSITION])
        if not 0 <= position <= 100:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="cover_position_out_of_range",
                translation_placeholders={"position": str(position)},
            )
        await self._async_send_command(build_go_to_level(self.where, position))

    def _handle_event(self, event: NormalizedEvent) -> None:
        if event.who != self.who or event.where != self.where:
            return

        if event.dimension == DIM_SHUTTER_STATUS:
            status = decode_shutter_status(event.values)
            if status is None:
                return
            self._attr_is_opening = status.is_opening
            self._attr_is_closing = status.is_closing
            self._attr_current_cover_position = status.position
            self._attr_is_closed = status.is_closed
            if self.hass is not None:
                self.async_write_ha_state()
            return

        if event.state == "opening":
            self._attr_is_opening = True
            self._attr_is_closing = False
        elif event.state == "closing":
            self._attr_is_opening = False
            self._attr_is_closing = True
        elif event.state == "stopped":
            self._attr_is_opening = False
            self._attr_is_closing = False
        else:
            return
        if self.hass is not None:
            self.async_write_ha_state()
