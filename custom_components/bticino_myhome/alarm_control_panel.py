"""BTicino burglar-alarm control panel via OpenWebNet WHO=5."""
from __future__ import annotations

import logging

from homeassistant.components.alarm_control_panel import AlarmControlPanelEntity
from homeassistant.components.alarm_control_panel.const import (
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import WHO_ALARM
from .data import BticinoConfigEntry
from .entity import BticinoEntity
from .gateway import BticinoGatewayError
from .platform import setup_dynamic_entities
from .protocol import (
    NormalizedEvent,
    alarm_arm_all,
    alarm_disarm_all,
    alarm_system_status_request,
)
from .protocol.alarm import ALARM_TRIGGER_WHATS, WHAT_SYSTEM_DISENGAGED, WHAT_SYSTEM_ENGAGED

_LOGGER = logging.getLogger(__name__)


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
        matches=lambda device: device.device_type == "alarm",
        factory=lambda device: BticinoAlarmControlPanel(
            gateway, device.who, device.where, device.name
        ),
    )


class BticinoAlarmControlPanel(BticinoEntity, AlarmControlPanelEntity):
    """WHO=5 central state plus legacy/reference-backed full arm/disarm control."""

    _attr_supported_features = AlarmControlPanelEntityFeature.ARM_AWAY
    _request_initial_state_on_add = True

    async def _async_request_initial_state(self) -> None:
        try:
            await self.gateway.async_send(
                alarm_system_status_request(), is_status_request=True
            )
        except BticinoGatewayError as err:
            _LOGGER.debug("WHO=5 alarm status request failed: %s", err)

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        await self._async_send_command(alarm_disarm_all())

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        await self._async_send_command(alarm_arm_all())

    def _handle_event(self, event: NormalizedEvent) -> None:
        if event.who != WHO_ALARM or event.what is None:
            return

        if event.what in ALARM_TRIGGER_WHATS:
            self._attr_alarm_state = AlarmControlPanelState.TRIGGERED
        elif event.where == "0" and event.what == WHAT_SYSTEM_ENGAGED:
            self._attr_alarm_state = AlarmControlPanelState.ARMED_AWAY
        elif event.where == "0" and event.what == WHAT_SYSTEM_DISENGAGED:
            self._attr_alarm_state = AlarmControlPanelState.DISARMED
        else:
            return

        if self.hass is not None:
            self.async_write_ha_state()
