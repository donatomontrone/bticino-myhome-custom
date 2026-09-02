"""BTicino 4200C alarm panel via OpenWebNet WHO=5."""
from __future__ import annotations

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    CodeFormat,
)
from homeassistant.components.alarm_control_panel.const import AlarmControlPanelState
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, WHO_ALARM
from .entity import BticinoEntity
from .protocol import alarm_arm_away, alarm_arm_home, alarm_disarm


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    runtime = entry.runtime_data
    gateway = runtime.gateway
    manager = runtime.device_manager
    known = {d.key for d in manager.devices if d.device_type == "alarm"}

    initial = [
        Bticino4200C(gateway, d.who, d.where, d.name)
        for d in manager.devices
        if d.device_type == "alarm"
    ]
    async_add_entities(initial)

    def _device_added(device) -> None:
        if device.device_type != "alarm" or device.key in known:
            return
        known.add(device.key)
        async_add_entities([Bticino4200C(gateway, device.who, device.where, device.name)])

    entry.async_on_unload(manager.add_listener(_device_added))


class Bticino4200C(BticinoEntity, AlarmControlPanelEntity):
    _attr_device_class = AlarmControlPanelEntity
    _attr_code_format = CodeFormat.NUMBER
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_HOME
        | AlarmControlPanelEntityFeature.ARM_AWAY
        | AlarmControlPanelEntityFeature.TRIGGER
    )

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        await self.gateway.async_send(alarm_disarm(int(self.where)))
        self.async_write_ha_state()

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        await self.gateway.async_send(alarm_arm_home(int(self.where)))
        self.async_write_ha_state()

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        await self.gateway.async_send(alarm_arm_away(int(self.where)))
        self.async_write_ha_state()

    async def async_alarm_trigger(self, code: str | None = None) -> None:
        self._attr_state = AlarmControlPanelState.TRIGGERED
        self.async_write_ha_state()
