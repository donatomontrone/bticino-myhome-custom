"""Tests for BTicino MyHome config-flow identity and inventory helpers."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock

from custom_components.bticino_myhome import _device_key_from_registry_entry
from custom_components.bticino_myhome.config_flow import (
    BticinoMyHomeConfigFlow,
    BticinoMyHomeOptionsFlow,
    _gateway_from_entry,
    _gateway_identity_conflicts,
    _gateway_with_entry_metadata,
    _merge_gateway_info,
)
from custom_components.bticino_myhome.const import (
    CONF_DEVICES,
    CONF_GATEWAY_HOST,
    CONF_GATEWAY_ID,
    CONF_GATEWAY_PORT,
    CONF_GATEWAY_SERIAL,
    CONF_GATEWAY_UDN,
)
from custom_components.bticino_myhome.device import BticinoDeviceManager
from custom_components.bticino_myhome.discovery import (
    DiscoveredDevice,
    DiscoveredGateway,
)
from custom_components.bticino_myhome.gateway import BticinoGateway


def test_config_flow_version_and_options_flow() -> None:
    assert BticinoMyHomeConfigFlow.VERSION == 3
    assert isinstance(BticinoMyHomeOptionsFlow(), BticinoMyHomeOptionsFlow)


def test_entry_data_prefers_stable_serial_identity() -> None:
    gateway = DiscoveredGateway(
        host="192.168.1.20",
        port=20000,
        serial="00:03:50:AA:BB:CC",
        model="MH201",
    )
    data = BticinoMyHomeConfigFlow._entry_data(gateway, "secret")
    assert data[CONF_GATEWAY_ID] == "serial:00:03:50:aa:bb:cc"
    assert data[CONF_GATEWAY_SERIAL] == "00:03:50:AA:BB:CC"
    assert data[CONF_GATEWAY_HOST] == "192.168.1.20"
    assert data[CONF_GATEWAY_PORT] == 20000


def test_ssdp_and_ownd_metadata_merge_keeps_ssdp_host() -> None:
    ssdp = DiscoveredGateway(
        host="192.168.1.20", serial="SERIAL", model="MH201"
    )
    ownd = DiscoveredGateway(
        host="192.168.1.21",
        port=20001,
        udn="uuid:test",
        firmware="1.2.3",
    )
    merged = _merge_gateway_info(ssdp, ownd)
    assert merged.host == "192.168.1.20"
    assert merged.port == 20001
    assert merged.serial == "SERIAL"
    assert merged.udn == "uuid:test"
    assert merged.firmware == "1.2.3"


def test_reconfigure_detects_conflicting_stable_serial() -> None:
    entry = SimpleNamespace(
        unique_id="serial:gateway-a",
        data={
            CONF_GATEWAY_HOST: "192.168.1.20",
            CONF_GATEWAY_PORT: 20000,
            CONF_GATEWAY_SERIAL: "gateway-a",
        },
    )
    candidate = DiscoveredGateway(
        host="192.168.1.21",
        port=20000,
        serial="gateway-b",
    )
    assert _gateway_identity_conflicts(entry, candidate)


def test_reconfigure_accepts_changed_ip_without_contradictory_identity() -> None:
    entry = SimpleNamespace(
        unique_id="serial:gateway-a",
        data={
            CONF_GATEWAY_HOST: "192.168.1.20",
            CONF_GATEWAY_PORT: 20000,
            CONF_GATEWAY_SERIAL: "gateway-a",
            CONF_GATEWAY_UDN: "uuid:gateway-a",
        },
    )
    candidate = DiscoveredGateway(
        host="192.168.1.21",
        port=20000,
        udn="uuid:gateway-a",
    )
    assert not _gateway_identity_conflicts(entry, candidate)
    merged = _gateway_with_entry_metadata(entry, candidate)
    assert merged.host == "192.168.1.21"
    assert merged.serial == "gateway-a"
    assert merged.udn == "uuid:gateway-a"


def test_gateway_from_entry_preserves_stable_metadata() -> None:
    entry = SimpleNamespace(
        data={
            CONF_GATEWAY_HOST: "mh201.local",
            CONF_GATEWAY_PORT: 20000,
            CONF_GATEWAY_SERIAL: "SERIAL",
            CONF_GATEWAY_UDN: "uuid:mh201",
        }
    )
    gateway = _gateway_from_entry(entry)
    assert gateway.host == "mh201.local"
    assert gateway.identity == "serial:serial"


def test_registry_device_key_parser_handles_colons_in_gateway_identity() -> None:
    device_entry = SimpleNamespace(
        identifiers={
            (
                "bticino_myhome",
                "serial:00:03:50:aa:bb:cc:1:12",
            )
        }
    )
    key = _device_key_from_registry_entry(
        device_entry, "serial:00:03:50:aa:bb:cc"
    )
    assert key == "1-12"


def test_options_flow_removes_inventory_device_and_persists() -> None:
    async def scenario() -> None:
        device = DiscoveredDevice.from_manual(
            who="1",
            where="1",
            device_type="light",
            name="Kitchen",
        )
        manager = BticinoDeviceManager([device])
        gateway = BticinoGateway(
            "127.0.0.1",
            20000,
            "",
            identity="serial:test",
        )
        entry = SimpleNamespace(
            entry_id="entry-id",
            runtime_data=SimpleNamespace(
                gateway=gateway,
                device_manager=manager,
            ),
            data={CONF_DEVICES: manager.as_dicts()},
        )
        hass = MagicMock()
        hass.config_entries.async_get_known_entry.return_value = entry

        flow = BticinoMyHomeOptionsFlow()
        flow.hass = hass
        flow.handler = entry.entry_id
        flow._remove_device_registry_entry = MagicMock()

        await flow.async_step_remove_device({"devices": ["1-1"]})

        assert manager.get("1-1") is None
        flow._remove_device_registry_entry.assert_called_once_with(device)
        hass.config_entries.async_update_entry.assert_called_once()
        persisted = hass.config_entries.async_update_entry.call_args.kwargs[
            "data"
        ]
        assert persisted[CONF_DEVICES] == []

    asyncio.run(scenario())
