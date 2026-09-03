"""Typed runtime data for the BTicino MyHome integration."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry

from .device import BticinoDeviceManager
from .gateway import BticinoGateway


@dataclass(slots=True)
class BticinoMyHomeData:
    """Runtime objects owned by one BTicino MyHome config entry."""

    gateway: BticinoGateway
    device_manager: BticinoDeviceManager


type BticinoConfigEntry = ConfigEntry[BticinoMyHomeData]
