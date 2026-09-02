"""BTicino 4200C alarm panel via OpenWebNet WHO=5."""
from __future__ import annotations

from homeassistant.components.alarm_control_panel import AlarmControlPanelEntity, AlarmControlPanelEntityFeature, CodeFormat
from homeassistant.components.alarm_control_panel.const import AlarmControlPanelState
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, WHO_ALARM
from .protocol import alarm_arm_away, alarm_arm_home, alarm_disarm
from .entity import BticinoEntity


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
    _attr_supported_features = AlarmControlPanelEntityFeature.ARM_AWAY | AlarmControlPanelEntityFeature.ARM_HOME
    _attr_code_format = CodeFormat.NUMBER

    def __init__(self, gateway, who: str, where: str, name: str) -> None:
        BticinoEntity.__init__(self, gateway, who, where, name or "Allarme 4200C")
        self._attr_unique_id = f"{DOMAIN}_{who}_{where}_alarm"
        self._attr_alarm_state = None

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        await self._gateway.async_send(alarm_arm_away(self._where))

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        await self._gateway.async_send(alarm_arm_home(self._where))

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        await self._gateway.async_send(alarm_disarm(self._where))

    def _handle_event(self, event) -> None:
        if event.who != WHO_ALARM or event.where != self._where:
            return
        states = {
            "disarmed": AlarmControlPanelState.DISARMED,
            "armed_away": AlarmControlPanelState.ARMED_AWAY,
            "armed_home": AlarmControlPanelState.ARMED_HOME,
            "triggered": AlarmControlPanelState.TRIGGERED,
        }
        state = states.get(event.state)
        if state is None:
            return
        self._attr_alarm_state = state
        self.async_write_ha_state()
