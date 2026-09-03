"""Constants for BTicino MyHome integration."""
from __future__ import annotations

from homeassistant.const import Platform

# Integration domain
DOMAIN = "bticino_myhome"

# Platforms
PLATFORMS = [
    Platform.ALARM_CONTROL_PANEL,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.CLIMATE,
    Platform.COVER,
    Platform.LIGHT,
    Platform.SCENE,
    Platform.SENSOR,
    Platform.SWITCH,
]

# Config entry keys
CONF_GATEWAY_HOST = "host"
CONF_GATEWAY_PORT = "port"
CONF_GATEWAY_PASSWORD = "password"
CONF_DEVICES = "devices"

# Defaults
DEFAULT_PORT = 20000
DEFAULT_NAME = "BTicino MyHome"

# WHO constants for device types
WHO_SCENARIO = 0
WHO_LIGHTING = 1
WHO_AUTOMATION = 2
WHO_THERMOREGULATION = 4
WHO_ALARM = 5
WHO_VIDEO_DOOR = 7
WHO_ENERGY = 18

# Minimum HA version
MIN_HA_VERSION = "2024.4.0"
