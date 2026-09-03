"""Diagnostics redaction tests."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace

from custom_components.bticino_myhome.diagnostics import (
    async_get_config_entry_diagnostics,
)
from custom_components.bticino_myhome.device import BticinoDeviceManager
from custom_components.bticino_myhome.discovery import DiscoveredDevice
from custom_components.bticino_myhome.gateway import BticinoGateway


def test_diagnostics_redact_network_identity_and_endpoint_names() -> None:
    async def scenario() -> None:
        gateway = BticinoGateway(
            "192.168.1.20",
            20000,
            "secret-password",
            identity="serial:00:03:50:aa:bb:cc",
        )
        device = DiscoveredDevice(
            who="4",
            where="1",
            device_type="climate",
            name="Camera da letto",
            capabilities=("temperature", "setpoint", "mode", "heating"),
            extra={
                "udn": "uuid:private-gateway",
                "serial": "PRIVATE-SERIAL",
                "macAddress": "00:03:50:AA:BB:CC",
            },
        )
        entry = SimpleNamespace(
            entry_id="entry-id",
            title="BTicino MH201 (192.168.1.20)",
            version=3,
            minor_version=1,
            runtime_data=SimpleNamespace(
                gateway=gateway,
                device_manager=BticinoDeviceManager([device]),
            ),
        )

        data = await async_get_config_entry_diagnostics(None, entry)
        rendered = repr(data)

        assert data["config_entry"] == {
            "entry_id": "entry-id",
            "version": 3,
            "minor_version": 1,
        }
        assert data["gateway"]["port"] == 20000
        assert data["devices"][0]["who"] == "4"
        assert data["devices"][0]["where"] == "1"
        assert "192.168.1.20" not in rendered
        assert "secret-password" not in rendered
        assert "00:03:50:aa:bb:cc" not in rendered.lower()
        assert "uuid:private-gateway" not in rendered
        assert "PRIVATE-SERIAL" not in rendered
        assert "Camera da letto" not in rendered

    asyncio.run(scenario())
