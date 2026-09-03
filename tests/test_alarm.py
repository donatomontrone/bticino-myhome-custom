"""Tests for the WHO=5 alarm-control, partition and diagnostic surfaces."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, call

from homeassistant.components.alarm_control_panel.const import AlarmControlPanelState

from custom_components.bticino_myhome.alarm_control_panel import BticinoAlarmControlPanel
from custom_components.bticino_myhome.binary_sensor import (
    BticinoAlarmBatteryProblemSensor,
    BticinoAlarmNetworkConnectivitySensor,
    BticinoAlarmPartitionSensor,
    BticinoAlarmTechnicalAlarmSensor,
)
from custom_components.bticino_myhome.gateway import BticinoGateway
from custom_components.bticino_myhome.protocol import normalize_frame, parse_frame


def _gateway() -> BticinoGateway:
    gateway = BticinoGateway("127.0.0.1", 20000, "pwd", identity="serial:test")
    gateway.async_send = AsyncMock()
    return gateway


def _event(raw: str):  # type: ignore[no-untyped-def]
    frame = parse_frame(raw)
    assert frame is not None
    return normalize_frame(frame)


def test_alarm_arm_disarm_use_reference_frames_without_optimistic_state() -> None:
    async def scenario() -> None:
        gateway = _gateway()
        panel = BticinoAlarmControlPanel(gateway, "5", "0", "4200C")

        panel._handle_event(_event("*5*9**##"))
        assert panel.state == AlarmControlPanelState.DISARMED
        await panel.async_alarm_arm_away()
        assert panel.state == AlarmControlPanelState.DISARMED
        gateway.async_send.assert_awaited_once_with("*5*8##")

        panel._handle_event(_event("*5*8**##"))
        assert panel.state == AlarmControlPanelState.ARMED_AWAY
        gateway.async_send.reset_mock()
        await panel.async_alarm_disarm()
        assert panel.state == AlarmControlPanelState.ARMED_AWAY
        gateway.async_send.assert_awaited_once_with("*5*9##")

    asyncio.run(scenario())


def test_alarm_initial_hydration_uses_complete_system_status() -> None:
    async def scenario() -> None:
        gateway = _gateway()
        panel = BticinoAlarmControlPanel(gateway, "5", "0", "4200C")

        await panel._async_request_initial_state()

        assert gateway.async_send.await_args_list == [
            call("*#5*0##", is_status_request=True)
        ]

    asyncio.run(scenario())


def test_alarm_system_and_alarm_events_update_panel_state() -> None:
    panel = BticinoAlarmControlPanel(_gateway(), "5", "0", "4200C")

    panel._handle_event(_event("*5*8**##"))
    assert panel.state == AlarmControlPanelState.ARMED_AWAY

    panel._handle_event(_event("*5*15*#2##"))
    assert panel.state == AlarmControlPanelState.TRIGGERED

    panel._handle_event(_event("*5*9**##"))
    assert panel.state == AlarmControlPanelState.DISARMED


def test_alarm_partition_sensor_hydrates_and_tracks_active_state() -> None:
    async def scenario() -> None:
        gateway = _gateway()
        partition = BticinoAlarmPartitionSensor(gateway, "0", "4200C", 3)

        await partition._async_request_initial_state()
        gateway.async_send.assert_awaited_once_with(
            "*#5*#3##", is_status_request=True
        )

        partition._handle_event(_event("*5*11*#3##"))
        assert partition.is_on is True

        partition._handle_event(_event("*5*18*#3##"))
        assert partition.is_on is False

    asyncio.run(scenario())


def test_alarm_partition_sensor_ignores_other_partitions() -> None:
    partition = BticinoAlarmPartitionSensor(_gateway(), "0", "4200C", 3)
    partition._handle_event(_event("*5*11*#2##"))
    assert partition.is_on is None


def test_alarm_battery_diagnostic_tracks_fault_ok_and_unloaded() -> None:
    async def scenario() -> None:
        gateway = _gateway()
        sensor = BticinoAlarmBatteryProblemSensor(gateway, "0", "4200C")

        await sensor._async_request_initial_state()
        gateway.async_send.assert_awaited_once_with(
            "*#5*0##", is_status_request=True
        )

        sensor._handle_event(_event("*5*4**##"))
        assert sensor.is_on is True
        sensor._handle_event(_event("*5*5**##"))
        assert sensor.is_on is False
        sensor._handle_event(_event("*5*10**##"))
        assert sensor.is_on is True

    asyncio.run(scenario())


def test_alarm_network_diagnostic_tracks_connectivity() -> None:
    sensor = BticinoAlarmNetworkConnectivitySensor(_gateway(), "0", "4200C")

    sensor._handle_event(_event("*5*6**##"))
    assert sensor.is_on is False
    sensor._handle_event(_event("*5*7**##"))
    assert sensor.is_on is True


def test_alarm_technical_alarm_tracks_only_its_auxiliary() -> None:
    sensor = BticinoAlarmTechnicalAlarmSensor(_gateway(), "0", "4200C", 2)

    sensor._handle_event(_event("*5*12*#3##"))
    assert sensor.is_on is None

    sensor._handle_event(_event("*5*12*#2##"))
    assert sensor.is_on is True

    sensor._handle_event(_event("*5*13*#2##"))
    assert sensor.is_on is False
