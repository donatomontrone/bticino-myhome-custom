"""Tests for the WHO=4 climate entity."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

from homeassistant.components.climate import HVACMode

from custom_components.bticino_myhome.climate import PRESET_ECO, BticinoClimate
from custom_components.bticino_myhome.gateway import BticinoGateway
from custom_components.bticino_myhome.protocol import normalize_frame, parse_frame


def _climate() -> tuple[BticinoClimate, BticinoGateway]:
    gateway = BticinoGateway("127.0.0.1", 20000, "pwd")
    gateway.async_send = AsyncMock()
    return BticinoClimate(gateway, "4", "1", "Thermostat 1"), gateway


def test_set_hvac_mode_and_temperature_frames() -> None:
    async def scenario() -> None:
        climate, gateway = _climate()
        await climate.async_set_hvac_mode(HVACMode.HEAT)
        gateway.async_send.assert_awaited_once_with("*4*110*1##")
        gateway.async_send.reset_mock()
        await climate.async_set_temperature(temperature=21.5)
        gateway.async_send.assert_awaited_once_with("*#4*1*#14*0215##")
        assert climate.target_temperature == 21.5

    asyncio.run(scenario())


def test_eco_is_a_preset_not_an_hvac_mode() -> None:
    async def scenario() -> None:
        climate, gateway = _climate()
        assert climate.hvac_modes == [
            HVACMode.OFF,
            HVACMode.HEAT,
            HVACMode.COOL,
            HVACMode.AUTO,
        ]
        await climate.async_set_hvac_mode(HVACMode.HEAT)
        gateway.async_send.reset_mock()
        await climate.async_set_preset_mode(PRESET_ECO)
        gateway.async_send.assert_awaited_once_with("*4*102*1##")
        assert climate.preset_mode == PRESET_ECO

    asyncio.run(scenario())


def test_climate_updates_from_dimension_events() -> None:
    climate, _ = _climate()
    frame = parse_frame("*#4*1*0*0225##")
    assert frame is not None
    climate._handle_event(normalize_frame(frame))
    assert climate.current_temperature == 22.5

    frame = parse_frame("*#4*1*14*0200##")
    assert frame is not None
    climate._handle_event(normalize_frame(frame))
    assert climate.target_temperature == 20.0


def test_climate_updates_from_mode_event() -> None:
    climate, _ = _climate()
    frame = parse_frame("*4*210*1##")
    assert frame is not None
    climate._handle_event(normalize_frame(frame))
    assert climate.hvac_mode == HVACMode.COOL
