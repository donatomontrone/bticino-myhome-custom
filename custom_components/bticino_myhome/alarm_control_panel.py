"""BTicino 4200C alarm panel via OpenWebNet WHO=5."""
from __future__ import annotations

from homeassistant.components.alarm_control_panel import AlarmControlPanelEntity, AlarmControlPanelEntityFeature, CodeFormat
from homeassistant.components.alarm_control_panel.const import AlarmControlPanelState
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, WHO_ALARM
from .entity import BticinoEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    gateway = entry.runtime_data.gateway
    devices = entry.runtime_data.device_manager.devices
    async_add_entities(
        [Bticino4200C(gateway, d.who, d.where, d.name) for d in devices if d.device_type == "alarm"]
    )


class Bticino4200C(BticinoEntity, AlarmControlPanelEntity):
    _attr_supported_features = AlarmControlPanelEntityFeature.ARM_AWAY | AlarmControlPanelEntityFeature.ARM_HOME
    _attr_code_format = CodeFormat.NUMBER

    def __init__(self, gateway, who: str, where: str, name: str) -> None:
        BticinoEntity.__init__(self, gateway, who, where, name or "Allarme 4200C")
        self._attr_unique_id = f"{DOMAIN}_{who}_{where}_alarm"
        self._attr_alarm_state = None

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        await self._gateway.async_send(f"*{WHO_ALARM}*1*{self._where}##")

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        await self._gateway.async_send(f"*{WHO_ALARM}*3*{self._where}##")

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        await self._gateway.async_send(f"*{WHO_ALARM}*0*{self._where}##")

    def _handle_raw_event(self, raw_message: str) -> None:
        raw = raw_message.strip()
        if raw == f"*{WHO_ALARM}*0*{self._where}##":
            self._attr_alarm_state = AlarmControlPanelState.DISARMED
        elif raw == f"*{WHO_ALARM}*1*{self._where}##":
            self._attr_alarm_state = AlarmControlPanelState.ARMED_AWAY
        elif raw == f"*{WHO_ALARM}*3*{self._where}##":
            self._attr_alarm_state = AlarmControlPanelState.ARMED_HOME
        elif raw == f"*{WHO_ALARM}*4*{self._where}##":
            self._attr_alarm_state = AlarmControlPanelState.TRIGGERED
        else:
            return
        self.async_write_ha_state()
