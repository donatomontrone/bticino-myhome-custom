"""Tests for BTicino MyHome config-flow identity helpers."""
from __future__ import annotations

from custom_components.bticino_myhome.config_flow import (
    BticinoMyHomeConfigFlow,
    BticinoMyHomeOptionsFlow,
    _merge_gateway_info,
)
from custom_components.bticino_myhome.const import (
    CONF_GATEWAY_HOST,
    CONF_GATEWAY_ID,
    CONF_GATEWAY_PORT,
    CONF_GATEWAY_SERIAL,
)
from custom_components.bticino_myhome.discovery import DiscoveredGateway


def test_config_flow_version_and_options_flow() -> None:
    assert BticinoMyHomeConfigFlow.VERSION == 3
    assert isinstance(BticinoMyHomeOptionsFlow(), BticinoMyHomeOptionsFlow)


def test_entry_data_prefers_stable_serial_identity() -> None:
    gateway = DiscoveredGateway(host="192.168.1.20", port=20000, serial="00:03:50:AA:BB:CC", model="MH201")
    data = BticinoMyHomeConfigFlow._entry_data(gateway, "secret")
    assert data[CONF_GATEWAY_ID] == "serial:00:03:50:aa:bb:cc"
    assert data[CONF_GATEWAY_SERIAL] == "00:03:50:AA:BB:CC"
    assert data[CONF_GATEWAY_HOST] == "192.168.1.20"
    assert data[CONF_GATEWAY_PORT] == 20000


def test_ssdp_and_ownd_metadata_merge_keeps_ssdp_host() -> None:
    ssdp = DiscoveredGateway(host="192.168.1.20", serial="SERIAL", model="MH201")
    ownd = DiscoveredGateway(host="192.168.1.21", port=20001, udn="uuid:test", firmware="1.2.3")
    merged = _merge_gateway_info(ssdp, ownd)
    assert merged.host == "192.168.1.20"
    assert merged.port == 20001
    assert merged.serial == "SERIAL"
    assert merged.udn == "uuid:test"
    assert merged.firmware == "1.2.3"
