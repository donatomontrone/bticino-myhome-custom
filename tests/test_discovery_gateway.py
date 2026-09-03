"""Tests for gateway discovery metadata."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

from custom_components.bticino_myhome.discovery import BticinoDiscovery, DiscoveredGateway


def test_gateway_identity_prefers_stable_metadata() -> None:
    assert DiscoveredGateway("192.168.1.10", serial="AA:BB").identity == "serial:aa:bb"
    assert DiscoveredGateway("192.168.1.10", udn="UUID:MH201").identity == "udn:uuid:mh201"
    assert DiscoveredGateway("MH201.LOCAL", 20000).identity == "mh201.local:20000"


def test_gateway_discovery_uses_ownd_find_gateways() -> None:
    async def scenario() -> None:
        raw = {
            "address": "192.168.1.20",
            "port": 20000,
            "serialNumber": "00:03:50:AA:BB:CC",
            "UDN": "uuid:mh201",
            "modelName": "MH201",
            "modelNumber": "1.0",
            "manufacturer": "BTicino S.p.A.",
        }
        with patch(
            "custom_components.bticino_myhome.discovery.find_gateways",
            new=AsyncMock(return_value=[raw]),
        ) as discover:
            gateways = await BticinoDiscovery.discover_gateways(timeout=1)

        discover.assert_awaited_once()
        assert len(gateways) == 1
        gateway = gateways[0]
        assert gateway.host == "192.168.1.20"
        assert gateway.identity == "serial:00:03:50:aa:bb:cc"
        assert gateway.model == "MH201"

    asyncio.run(scenario())
