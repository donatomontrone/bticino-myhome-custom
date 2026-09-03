"""Test BTicino MyHome config flow structure."""
from __future__ import annotations

from custom_components.bticino_myhome.config_flow import (
    BticinoMyHomeConfigFlow,
    BticinoMyHomeOptionsFlow,
)


def test_config_flow_version_and_options_flow() -> None:
    assert BticinoMyHomeConfigFlow.VERSION == 2
    assert isinstance(BticinoMyHomeOptionsFlow(), BticinoMyHomeOptionsFlow)
