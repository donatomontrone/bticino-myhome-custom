"""BTicino alarm control panel via OpenWebNet WHO=5."""
from __future__ import annotations

from homeassistant.components.alarm_control_panel import AlarmControlPanelEntity
from homeassistant.components.alarm_control_panel.const import (
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .data import BticinoConfigEntry
from .entity import BticinoEntity
from .platform import setup_dynamic_entities
from .protocol import NormalizedEvent, alarm_arm_away, alarm_arm_home, alarm_disarm


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
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_HOME | AlarmControlPanelEntityFeature.ARM_AWAY
    )

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        await self._async_send_command(alarm_disarm(self.where))

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        await self._async_send_command(alarm_arm_home(self.where))

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        await self._async_send_command(alarm_arm_away(self.where))

    def _handle_event(self, event: NormalizedEvent) -> None:
        if event.who != self.who or event.where != self.where or event.state is None:
            return
        states = {
            "disarmed": AlarmControlPanelState.DISARMED,
            "armed_home": AlarmControlPanelState.ARMED_HOME,
            "armed_away": AlarmControlPanelState.ARMED_AWAY,
            "triggered": AlarmControlPanelState.TRIGGERED,
        }
        state = states.get(event.state)
        if state is None:
            return
        self._attr_state = state
        if self.hass is not None:
            self.async_write_ha_state()
