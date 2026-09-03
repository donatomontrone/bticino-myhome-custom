"""Constants for the BTicino MyHome MH201 integration."""
from __future__ import annotations

DOMAIN = "bticino_myhome"

CONF_GATEWAY_HOST = "host"
CONF_GATEWAY_PORT = "port"
CONF_GATEWAY_PASSWORD = "password"
CONF_GATEWAY_SERIAL = "serial"
CONF_DEVICES = "devices"

DEFAULT_PORT = 20000
DEFAULT_NAME = "BTicino MyHome"
EVENT_OPENWEBNET = f"{DOMAIN}_event"

# OpenWebNet WHO families used by this integration.
WHO_SCENARIO = "0"
WHO_LIGHTING = "1"
WHO_AUTOMATION = "2"
WHO_LOAD_MANAGEMENT = "3"
WHO_THERMOREGULATION = "4"
WHO_ALARM = "5"
WHO_VIDEO_DOOR_ENTRY = "7"
WHO_DIAGNOSTIC = "13"
WHO_ENERGY_MANAGEMENT = "18"

WHAT_VDE_CALL_START = "21"
WHAT_VDE_CALL_END_1 = "22"
WHAT_VDE_CALL_END_2 = "23"
WHAT_VDE_LOCK_RELEASE = "10"

PLATFORMS = [
    "scene",
    "light",
    "cover",
    "switch",
    "climate",
    "alarm_control_panel",
    "binary_sensor",
    "sensor",
    "button",
]

SCENARIO_ADDRESS_RANGE = range(1, 31)
SCAN_TIMEOUT = 30
STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}_devices"
