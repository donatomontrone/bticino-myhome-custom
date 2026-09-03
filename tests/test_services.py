"""Tests for BTicino MyHome services."""
from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from custom_components.bticino_myhome.const import DOMAIN
from custom_components.bticino_myhome.gateway import BticinoGateway


@pytest.fixture
async def mock_gateway(hass: HomeAssistant) -> BticinoGateway:
    """Create a mock gateway."""
    gateway = BticinoGateway(host="127.0.0.1", port=20000, password="pwd")
    return gateway


async def test_send_frame_service_success(hass: HomeAssistant, mock_gateway: BticinoGateway) -> None:
    """Test send_frame service with valid frame."""
    # Setup
    hass.data.setdefault(DOMAIN, {})
    entry_id = "test_entry"
    hass.data[DOMAIN][entry_id] = {"gateway": mock_gateway}

    # Mock async_send
    mock_gateway.async_send = pytest.helpers.async_mock()

    # Call service
    await hass.services.async_call(
        DOMAIN,
        "send_frame",
        {"frame": "*1*1*21##"},
        blocking=True,
    )

    # Verify
    mock_gateway.async_send.assert_called_once_with("*1*1*21##", is_status_request=False)


async def test_send_frame_service_with_status_request(hass: HomeAssistant, mock_gateway: BticinoGateway) -> None:
    """Test send_frame service with status request."""
    # Setup
    hass.data.setdefault(DOMAIN, {})
    entry_id = "test_entry"
    hass.data[DOMAIN][entry_id] = {"gateway": mock_gateway}

    # Mock async_send
    mock_gateway.async_send = pytest.helpers.async_mock()

    # Call service
    await hass.services.async_call(
        DOMAIN,
        "send_frame",
        {"frame": "*1*1*21##", "is_status_request": True},
        blocking=True,
    )

    # Verify
    mock_gateway.async_send.assert_called_once_with("*1*1*21##", is_status_request=True)


async def test_send_frame_service_missing_frame(hass: HomeAssistant) -> None:
    """Test send_frame service with missing frame."""
    # Setup
    hass.data.setdefault(DOMAIN, {})
    entry_id = "test_entry"
    gateway = BticinoGateway(host="127.0.0.1", port=20000, password="pwd")
    hass.data[DOMAIN][entry_id] = {"gateway": gateway}

    # Call service and expect error
    with pytest.raises(HomeAssistantError, match="Frame is required"):
        await hass.services.async_call(
            DOMAIN,
            "send_frame",
            {},
            blocking=True,
        )


async def test_send_frame_service_no_gateway(hass: HomeAssistant) -> None:
    """Test send_frame service with no gateway."""
    # Setup
    hass.data.setdefault(DOMAIN, {})

    # Call service and expect error
    with pytest.raises(HomeAssistantError, match="No gateway configured"):
        await hass.services.async_call(
            DOMAIN,
            "send_frame",
            {"frame": "*1*1*21##"},
            blocking=True,
        )
