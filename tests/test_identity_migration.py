"""Tests for stable gateway identity migration."""
from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

from custom_components.bticino_myhome import async_migrate_entry
from custom_components.bticino_myhome.const import CONF_GATEWAY_ID


def test_version_two_migration_preserves_legacy_entity_identity() -> None:
    async def scenario() -> None:
        hass = MagicMock()
        entry = MagicMock()
        entry.version = 2
        entry.unique_id = "192.168.1.20:20000"
        entry.data = {
            "host": "192.168.1.20",
            "port": 20000,
            "password": "",
            "devices": [],
        }

        assert await async_migrate_entry(hass, entry) is True
        kwargs = hass.config_entries.async_update_entry.call_args.kwargs
        assert kwargs["version"] == 3
        assert kwargs["data"][CONF_GATEWAY_ID] == "192.168.1.20:20000"

    asyncio.run(scenario())
