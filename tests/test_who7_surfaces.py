"""Tests for conservative WHO=7 entity exposure."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock

from homeassistant.helpers.entity import EntityCategory

from custom_components.bticino_myhome.binary_sensor import (
    async_setup_entry as setup_binary_sensor,
)
from custom_components.bticino_myhome.device import BticinoDeviceManager
from custom_components.bticino_myhome.discovery import DiscoveredDevice
from custom_components.bticino_myhome.gateway import BticinoGateway
from custom_components.bticino_myhome.sensor import (
    BticinoIntercomEventLog,
    async_setup_entry as setup_sensor,
)


def _entry(manager: BticinoDeviceManager):
    gateway = BticinoGateway("127.0.0.1", 20000, "pwd")
    entry = MagicMock()
    entry.runtime_data = SimpleNamespace(gateway=gateway, device_manager=manager)
    return entry


def test_no_synthetic_who7_entities_without_inventory_evidence() -> None:
    async def scenario() -> None:
        manager = BticinoDeviceManager()
        entry = _entry(manager)
        add_binary = MagicMock()
        add_sensor = MagicMock()

        await setup_binary_sensor(MagicMock(), entry, add_binary)
        await setup_sensor(MagicMock(), entry, add_sensor)

        add_binary.assert_not_called()
        add_sensor.assert_not_called()

    asyncio.run(scenario())


def test_raw_who7_sensor_is_gateway_diagnostic_and_disabled_by_default() -> None:
    async def scenario() -> None:
        manager = BticinoDeviceManager(
            [
                DiscoveredDevice.from_manual(
                    who="7",
                    where="12",
                    device_type="intercom",
                    name="Entrance intercom",
                )
            ]
        )
        entry = _entry(manager)
        add_sensor = MagicMock()

        await setup_sensor(MagicMock(), entry, add_sensor)

        entities = add_sensor.call_args.args[0]
        assert len(entities) == 1
        entity = entities[0]
        assert isinstance(entity, BticinoIntercomEventLog)
        assert entity.entity_category == EntityCategory.DIAGNOSTIC
        assert entity.entity_registry_enabled_default is False
        assert entity.unique_id == f"{entry.runtime_data.gateway.identity}:who7_raw_event"

    asyncio.run(scenario())
