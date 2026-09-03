"""BTicino MyHome constants."""

DOMAIN = "bticino_myhome"
MANUFACTURER = "BTicino"

# Config entry keys
CONF_GATEWAY_HOST = "host"
CONF_GATEWAY_PORT = "port"
CONF_GATEWAY_PASSWORD = "password"
CONF_DEVICES = "devices"

# Platforms
PLATFORMS = [
    "light",
    "cover",
    "switch",
    "scene",
    "alarm_control_panel",
    "button",
]

# WHO (What OpenWebNet)
WHO_SCENARIO = "0"
WHO_LIGHTING = "1"
WHO_AUTOMATION = "2"
WHO_CLIMATE = "4"
WHO_ALARM = "5"
WHO_ENERGY_MANAGEMENT = "18"
WHO_LOAD_MANAGEMENT = "16"
WHO_VIDEO_DOOR_ENTRY = "7"

# Compatible with Home Assistant 2025.1.0 and later
# Verified compatible with Home Assistant 2026.1+ (including 2026.6 requirement)
