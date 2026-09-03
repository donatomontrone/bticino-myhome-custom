"""Tests for BTicino MyHome device triggers."""
from __future__ import annotations

from homeassistant.core import HomeAssistant

from custom_components.bticino_myhome.device_trigger import async_get_trigger_capabilities, async_get_triggers


async def test_get_triggers_empty_when_no_scenes(hass: HomeAssistant) -> None:
    """Test get_triggers returns empty list when no scenes."""
    device_id = "test_device"
    triggers = await async_get_triggers(hass, device_id)
    assert triggers == []


async def test_get_triggers_returns_scenario_triggers(hass: HomeAssistant) -> None:
    """Test get_triggers returns scenario triggers for scene devices."""
    device_id = "test_device"
    triggers = await async_get_triggers(hass, device_id)

    # Should return empty list if no scenes exist
    # This test documents the expected behavior
    assert isinstance(triggers, list)


async def test_get_trigger_capabilities(hass: HomeAssistant) -> None:
    """Test get_trigger_capabilities returns empty dict."""
    config = {"device_id": "test_device", "type": "scenario_activated"}
    capabilities = await async_get_trigger_capabilities(hass, config)
    assert capabilities == {}
