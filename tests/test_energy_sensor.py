"""Tests for the WHO=18 active-power sensor."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, call

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfPower

from custom_components.bticino_myhome.gateway import BticinoGateway, BticinoGatewayError
from custom_components.bticino_myhome.protocol import normalize_frame, parse_frame
from custom_components.bticino_myhome.sensor import BticinoActivePowerSensor


def _sensor() -> tuple[BticinoActivePowerSensor, BticinoGateway]:
    gateway = BticinoGateway("127.0.0.1", 20000, "pwd")
    gateway.async_send = AsyncMock()
    return BticinoActivePowerSensor(gateway, "18", "51", "Energy 51"), gateway


def _event(raw: str):  # type: ignore[no-untyped-def]
    frame = parse_frame(raw)
    assert frame is not None
    return normalize_frame(frame)


def test_active_power_sensor_metadata_is_read_only_power() -> None:
    sensor, _ = _sensor()

    assert sensor.device_class == SensorDeviceClass.POWER
    assert sensor.native_unit_of_measurement == UnitOfPower.WATT
    assert sensor.state_class == SensorStateClass.MEASUREMENT
    assert sensor.native_value is None
    assert sensor.should_poll is False


def test_active_power_initial_hydration_requests_dim113() -> None:
    async def scenario() -> None:
        sensor, gateway = _sensor()

        await sensor._async_request_initial_state()

        assert gateway.async_send.await_args_list == [
            call("*#18*51*113##", is_status_request=True),
        ]
        assert sensor.native_value is None

    asyncio.run(scenario())


def test_active_power_hydration_failure_does_not_invent_state() -> None:
    async def scenario() -> None:
        sensor, gateway = _sensor()
        gateway.async_send.side_effect = BticinoGatewayError("unavailable")

        await sensor._async_request_initial_state()

        assert sensor.native_value is None

    asyncio.run(scenario())


def test_active_power_event_updates_watts() -> None:
    sensor, _ = _sensor()

    sensor._handle_event(_event("*#18*51*113*487##"))

    assert sensor.native_value == 487


def test_active_power_ignores_other_endpoint_dimension_and_invalid_value() -> None:
    sensor, _ = _sensor()
    sensor._handle_event(_event("*#18*51*113*487##"))

    sensor._handle_event(_event("*#18*52*113*900##"))
    sensor._handle_event(_event("*#18*51*53*1200##"))
    sensor._handle_event(_event("*#18*51*113*invalid##"))

    assert sensor.native_value == 487
