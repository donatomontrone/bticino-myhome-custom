"""Tests for the WHO=4 climate entity."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

from homeassistant.components.climate import HVACMode

from custom_components.bticino_myhome.climate import (
    PRESET_ANTIFREEZE,
    PRESET_GENERIC_PROTECTION,
    PRESET_THERMAL_PROTECTION,
    BticinoClimate,
)
from custom_components.bticino_myhome.gateway import BticinoGateway
from custom_components.bticino_myhome.protocol import normalize_frame, parse_frame


def _climate() -> tuple[BticinoClimate, BticinoGateway]:
    gateway = BticinoGateway("127.0.0.1", 20000, "pwd")
    gateway.async_send = AsyncMock()
    return BticinoClimate(gateway, "4", "1", "Thermostat 1"), gateway


def test_set_hvac_mode_and_temperature_frames_are_not_optimistic() -> None:
    async def scenario() -> None:
        climate, gateway = _climate()
        assert climate.hvac_mode is None
        assert climate.target_temperature is None

        await climate.async_set_hvac_mode(HVACMode.HEAT)
        gateway.async_send.assert_awaited_once_with("*4*110*#1##")
        assert climate.hvac_mode is None

        climate._attr_hvac_mode = HVACMode.HEAT
        gateway.async_send.reset_mock()
        await climate.async_set_temperature(temperature=21.5)
        gateway.async_send.assert_awaited_once_with("*#4*#1*#14*0215*1##")
        assert climate.target_temperature is None

    asyncio.run(scenario())


def test_protection_modes_are_explicit_presets_and_not_optimistic() -> None:
    async def scenario() -> None:
        climate, gateway = _climate()
        assert climate.preset_modes == [
            PRESET_ANTIFREEZE,
            PRESET_THERMAL_PROTECTION,
            PRESET_GENERIC_PROTECTION,
        ]
        await climate.async_set_preset_mode(PRESET_ANTIFREEZE)
        gateway.async_send.assert_awaited_once_with("*4*102*#1##")
        assert climate.preset_mode is None

    asyncio.run(scenario())


def test_set_temperature_uses_conditioning_and_generic_operation_modes() -> None:
    async def scenario() -> None:
        climate, gateway = _climate()

        climate._attr_hvac_mode = HVACMode.COOL
        await climate.async_set_temperature(temperature=20)
        gateway.async_send.assert_awaited_once_with("*#4*#1*#14*0200*2##")

        gateway.async_send.reset_mock()
        climate._attr_hvac_mode = HVACMode.AUTO
        await climate.async_set_temperature(temperature=19.5)
        gateway.async_send.assert_awaited_once_with("*#4*#1*#14*0195*3##")

    asyncio.run(scenario())


def test_climate_updates_from_dimension_events() -> None:
    climate, _ = _climate()
    frame = parse_frame("*#4*1*0*0225##")
    assert frame is not None
    climate._handle_event(normalize_frame(frame))
    assert climate.current_temperature == 22.5

    frame = parse_frame("*#4*1*14*0200*1##")
    assert frame is not None
    climate._handle_event(normalize_frame(frame))
    assert climate.target_temperature == 20.0


def test_climate_updates_from_mode_and_protection_events() -> None:
    climate, _ = _climate()

    frame = parse_frame("*4*210*1##")
    assert frame is not None
    climate._handle_event(normalize_frame(frame))
    assert climate.hvac_mode == HVACMode.COOL
    assert climate.preset_mode is None

    frame = parse_frame("*4*102*1##")
    assert frame is not None
    climate._handle_event(normalize_frame(frame))
    assert climate.hvac_mode == HVACMode.HEAT
    assert climate.preset_mode == PRESET_ANTIFREEZE

    frame = parse_frame("*4*202*1##")
    assert frame is not None
    climate._handle_event(normalize_frame(frame))
    assert climate.hvac_mode == HVACMode.COOL
    assert climate.preset_mode == PRESET_THERMAL_PROTECTION

    frame = parse_frame("*4*302*1##")
    assert frame is not None
    climate._handle_event(normalize_frame(frame))
    assert climate.hvac_mode == HVACMode.AUTO
    assert climate.preset_mode == PRESET_GENERIC_PROTECTION


def test_climate_accepts_central_zone_where_echoes() -> None:
    climate, _ = _climate()
    frame = parse_frame("*4*110*#1##")
    assert frame is not None
    climate._handle_event(normalize_frame(frame))
    assert climate.hvac_mode == HVACMode.HEAT
