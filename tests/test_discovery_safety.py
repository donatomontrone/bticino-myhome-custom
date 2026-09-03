"""Tests for conservative active discovery semantics."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest

from custom_components.bticino_myhome.discovery import BticinoDiscovery, DiscoverySource
from custom_components.bticino_myhome.gateway import (
    BticinoCommandResult,
    BticinoGateway,
    BticinoGatewayCommandRejected,
    BticinoGatewayConnectionError,
)


def _gateway() -> BticinoGateway:
    return BticinoGateway("127.0.0.1", 20000, "pwd")


def test_probe_correlates_only_matching_command_responses() -> None:
    async def scenario() -> None:
        gateway = _gateway()
        gateway.async_send = AsyncMock(
            return_value=BticinoCommandResult(
                True,
                ("*1*1*21##", "*2*1*22##"),
            )
        )
        discovery = BticinoDiscovery(gateway)
        await discovery._probe_status("1", "21")

        found = discovery._found["1-21"]
        assert found.source == DiscoverySource.ACTIVE.value
        assert found.extra["discovery"] == DiscoverySource.ACTIVE.value
        assert "2-22" not in discovery._found

    asyncio.run(scenario())


def test_probe_treats_nack_as_no_candidate_but_surfaces_transport_failure() -> None:
    async def scenario() -> None:
        gateway = _gateway()
        discovery = BticinoDiscovery(gateway)
        gateway.async_send = AsyncMock(
            side_effect=BticinoGatewayCommandRejected("nack")
        )
        await discovery._probe_status("1", "21")
        assert discovery._found == {}

        gateway.async_send = AsyncMock(
            side_effect=BticinoGatewayConnectionError("offline")
        )
        with pytest.raises(BticinoGatewayConnectionError, match="offline"):
            await discovery._probe_status("1", "21")

    asyncio.run(scenario())


def test_manual_known_who_rejects_impossible_device_type() -> None:
    with pytest.raises(ValueError, match="not valid"):
        BticinoDiscovery.from_manual(who="1", where="21", device_type="cover")

    advanced = BticinoDiscovery.from_manual(
        who="99", where="12", device_type="sensor", name="Custom"
    )
    assert advanced.device_type == "sensor"
