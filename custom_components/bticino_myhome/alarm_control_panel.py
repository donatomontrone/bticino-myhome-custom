"""BTicino alarm control panel via OpenWebNet WHO=5."""
from __future__ import annotations

from homeassistant.components.alarm_control_panel import AlarmControlPanelEntity
from homeassistant.components.alarm_control_panel.const import (
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import BticinoEntity
from .protocol import NormalizedEvent, alarm_arm_away, alarm_arm_home, alarm_disarm


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    runtime = entry.runtime_data
    gateway = runtime.gateway
    manager = runtime.device_manager
    known = {device.key for device in manager.devices if device.device_type == "alarm"}
    async_add_entities(
        [
            BticinoAlarmControlPanel(gateway, device.who, device.where, device.name)
            for device in manager.devices
            if device.device_type == "alarm"
        ]
    )

    def _device_added(device) -> None:
        if device.device_type != "alarm" or device.key in known:
            return
        known.add(device.key)
        async_add_entities(
            [BticinoAlarmControlPanel(gateway, device.who, device.where, device.name)]
        )

    entry.async_on_unload(manager.add_listener(_device_added))


class BticinoAlarmControlPanel(BticinoEntity, AlarmControlPanelEntity):
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_HOME | AlarmControlPanelEntityFeature.ARM_AWAY
    )

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        await self.gateway.async_send(alarm_disarm(self.where))

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        await self.gateway.async_send(alarm_arm_home(self.where))

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        await self.gateway.async_send(alarm_arm_away(self.where))

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
