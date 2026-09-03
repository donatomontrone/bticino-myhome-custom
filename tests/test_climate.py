"""Tests for BTicino MyHome climate platform."""
from __future__ import annotations

from unittest.mock import AsyncMock

from homeassistant.components.climate import ATTR_TARGET_TEMP_HIGH, ATTR_TARGET_TEMP_LOW, HVACMode
from homeassistant.const import ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant

from custom_components.bticino_myhome.climate import BticinoClimate
from custom_components.bticino_myhome.device import BticinoDevice
from custom_components.bticino_myhome.gateway import BticinoGateway


async def test_climate_set_hvac_mode_heat(hass: HomeAssistant) -> None:
    """Test setting HVAC mode to heat."""
    device = BticinoDevice(
        device_type="climate",
        device_id="thermo_1",
        unique_id="bticino_thermo_1",
        name="Thermostat 1",
        where="1",
        who=4,
    )

    gateway = BticinoGateway(host="127.0.0.1", port=20000, password="pwd")
    gateway.async_send = AsyncMock()

    climate = BticinoClimate(device, gateway)
    climate.hass = hass

    await climate.async_set_hvac_mode(HVACMode.HEAT)

    # Verify frame sent
    gateway.async_send.assert_called_once_with("*4*110*1##")
    assert climate.hvac_mode == HVACMode.HEAT


async def test_climate_set_hvac_mode_cool(hass: HomeAssistant) -> None:
    """Test setting HVAC mode to cool."""
    device = BticinoDevice(
        device_type="climate",
        device_id="thermo_1",
        unique_id="bticino_thermo_1",
        name="Thermostat 1",
        where="1",
        who=4,
    )

    gateway = BticinoGateway(host="127.0.0.1", port=20000, password="pwd")
    gateway.async_send = AsyncMock()

    climate = BticinoClimate(device, gateway)
    climate.hass = hass

    await climate.async_set_hvac_mode(HVACMode.COOL)

    # Verify frame sent
    gateway.async_send.assert_called_once_with("*4*210*1##")
    assert climate.hvac_mode == HVACMode.COOL


async def test_climate_set_hvac_mode_off(hass: HomeAssistant) -> None:
    """Test setting HVAC mode to off."""
    device = BticinoDevice(
        device_type="climate",
        device_id="thermo_1",
        unique_id="bticino_thermo_1",
        name="Thermostat 1",
        where="1",
        who=4,
    )

    gateway = BticinoGateway(host="127.0.0.1", port=20000, password="pwd")
    gateway.async_send = AsyncMock()

    climate = BticinoClimate(device, gateway)
    climate.hass = hass

    await climate.async_set_hvac_mode(HVACMode.OFF)

    # Verify frame sent
    gateway.async_send.assert_called_once_with("*4*303*1##")
    assert climate.hvac_mode == HVACMode.OFF


async def test_climate_set_temperature(hass: HomeAssistant) -> None:
    """Test setting target temperature."""
    device = BticinoDevice(
        device_type="climate",
        device_id="thermo_1",
        unique_id="bticino_thermo_1",
        name="Thermostat 1",
        where="1",
        who=4,
    )

    gateway = BticinoGateway(host="127.0.0.1", port=20000, password="pwd")
    gateway.async_send = AsyncMock()

    climate = BticinoClimate(device, gateway)
    climate.hass = hass

    await climate.async_set_temperature(temperature=21.5)

    # Verify frame sent (21.5 -> "0215")
    gateway.async_send.assert_called_once_with("*#4*1*#14*0215##")
    assert climate.target_temperature == 21.5


async def test_climate_update_from_temperature_event(hass: HomeAssistant) -> None:
    """Test updating from temperature event."""
    device = BticinoDevice(
        device_type="climate",
        device_id="thermo_1",
        unique_id="bticino_thermo_1",
        name="Thermostat 1",
        where="1",
        who=4,
    )

    gateway = BticinoGateway(host="127.0.0.1", port=20000, password="pwd")

    climate = BticinoClimate(device, gateway)
    climate.hass = hass

    # Simulate temperature event
    climate.update_from_event("temperature", {"temperature": 22.5})

    assert climate.current_temperature == 22.5


async def test_climate_update_from_setpoint_event(hass: HomeAssistant) -> None:
    """Test updating from setpoint event."""
    device = BticinoDevice(
        device_type="climate",
        device_id="thermo_1",
        unique_id="bticino_thermo_1",
        name="Thermostat 1",
        where="1",
        who=4,
    )

    gateway = BticinoGateway(host="127.0.0.1", port=20000, password="pwd")

    climate = BticinoClimate(device, gateway)
    climate.hass = hass

    # Simulate setpoint event
    climate.update_from_event("setpoint", {"setpoint": 20.0})

    assert climate.target_temperature == 20.0


async def test_climate_update_from_mode_event(hass: HomeAssistant) -> None:
    """Test updating from mode event."""
    device = BticinoDevice(
        device_type="climate",
        device_id="thermo_1",
        unique_id="bticino_thermo_1",
        name="Thermostat 1",
        where="1",
        who=4,
    )

    gateway = BticinoGateway(host="127.0.0.1", port=20000, password="pwd")

    climate = BticinoClimate(device, gateway)
    climate.hass = hass

    # Simulate mode event
    climate.update_from_event("mode", {"mode": "heat"})

    assert climate.hvac_mode == HVACMode.HEAT
