"""Entity action error-surface tests."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest
from homeassistant.exceptions import HomeAssistantError

from custom_components.bticino_myhome.gateway import (
    BticinoGateway,
    BticinoGatewayCommandError,
)
from custom_components.bticino_myhome.light import BticinoLight


def test_entity_transport_failure_is_translated_home_assistant_error() -> None:
    async def scenario() -> None:
        gateway = BticinoGateway("127.0.0.1", 20000, "")
        gateway.async_send = AsyncMock(
            side_effect=BticinoGatewayCommandError("command channel failed")
        )
        entity = BticinoLight(gateway, "1", "21", "Kitchen")

        with pytest.raises(HomeAssistantError) as error:
            await entity.async_turn_on()

        assert error.value.translation_domain == "bticino_myhome"
        assert error.value.translation_key == "entity_command_failed"
        assert error.value.translation_placeholders == {
            "detail": "command channel failed"
        }

    asyncio.run(scenario())
