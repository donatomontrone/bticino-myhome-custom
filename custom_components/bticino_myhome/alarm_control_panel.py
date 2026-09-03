"""BTicino MyHome alarm control panel."""
from __future__ import annotations

from typing import Any

from homeassistant.components.alarm_control_panel import AlarmControlPanelEntity
from homeassistant.components.alarm_control_panel.const import (
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import BticinoEntity
from .protocol import alarm_arm_away, alarm_arm_home, alarm_disarm


class BticinoAlarmControlPanel(BticinoEntity, AlarmControlPanelEntity):
    """Alarm control panel entity."""

    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_HOME
        | AlarmControlPanelEntityFeature.ARM_AWAY
    )

    def __init__(self, device: Any, gateway: Any) -> None:
        super().__init__(device, gateway)
        self._attr_state = AlarmControlPanelState.DISARMED

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        await alarm_disarm(self._gateway, self._device.who, self._device.address)

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        await alarm_arm_home(self._gateway, self._device.who, self._device.address)

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        await alarm_arm_away(self._gateway, self._device.who, self._device.address)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up alarm control panel from config entry."""
