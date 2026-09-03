"""Constants for the BTicino MyHome MH201 integration."""
from __future__ import annotations

DOMAIN = "bticino_myhome"

CONF_GATEWAY_HOST = "host"
CONF_GATEWAY_PORT = "port"
CONF_GATEWAY_PASSWORD = "password"
CONF_GATEWAY_ID = "gateway_id"
CONF_GATEWAY_SERIAL = "serial"
CONF_GATEWAY_UDN = "udn"
CONF_GATEWAY_MODEL = "model"
CONF_GATEWAY_FIRMWARE = "firmware"
CONF_GATEWAY_MANUFACTURER = "manufacturer"
CONF_DEVICES = "devices"

DEFAULT_PORT = 20000
DEFAULT_NAME = "BTicino MyHome"
EVENT_OPENWEBNET = f"{DOMAIN}_event"

# OpenWebNet WHO families used by this integration.
WHO_SCENARIO = "0"
WHO_LIGHTING = "1"
WHO_AUTOMATION = "2"
WHO_THERMOREGULATION = "4"
WHO_ALARM = "5"
WHO_DOOR_ENTRY = "6"
WHO_MULTIMEDIA = "7"
WHO_DIAGNOSTIC = "13"
WHO_ENERGY_MANAGEMENT = "18"

PLATFORMS = [
    "scene",
    "light",
    "cover",
    "climate",
    "alarm_control_panel",
    "binary_sensor",
    "sensor",
    "button",
]

SCAN_TIMEOUT = 30
STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}_devices"
