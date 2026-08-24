"""Costanti per l'integrazione BTicino MyHome (MH201 / OpenWebNet).

Verificato compatibile con Home Assistant 2026.1 e successivi (incluso il
requisito 2026.6 di non usare piu' `platform: template`: questa
integrazione usa esclusivamente Entity class native, mai template YAML).
"""

DOMAIN = "bticino_myhome"

CONF_GATEWAY_HOST = "host"
CONF_GATEWAY_PORT = "port"
CONF_GATEWAY_PASSWORD = "password"
CONF_GATEWAY_SERIAL = "serial"

DEFAULT_PORT = 20000

# WHO OpenWebNet - categorie di messaggi/dispositivi sul bus SCS
# Riferimento ufficiale: developer.legrand.com/local-interoperability
WHO_SCENARIO = "0"            # scenari configurati con Home+Project
WHO_LIGHTING = "1"
WHO_AUTOMATION = "2"          # tapparelle/tende
WHO_LOAD_MANAGEMENT = "3"     # gestione carichi
WHO_ALARM = "5"               # 4200C - centrale antifurto (BURGLAR ALARM)
WHO_VIDEO_DOOR_ENTRY = "7"    # citofono / Hometouch 7 (VIDEO DOOR ENTRY SYSTEM, WHO ufficiale 7)
WHO_ENERGY_MANAGEMENT = "18"
WHO_DIAGNOSTIC = "13"

# WHAT per WHO=7 (video door entry) - comandi principali documentati
WHAT_VDE_CALL_START = "21"
WHAT_VDE_CALL_END_1 = "22"
WHAT_VDE_CALL_END_2 = "23"
WHAT_VDE_LOCK_RELEASE = "10"   # apertura serratura elettrica

PLATFORMS = [
    "scene",
    "light",
    "cover",
    "switch",
    "alarm_control_panel",
    "binary_sensor",
    "sensor",
    "button",
]

# Range di indirizzi scenari tipicamente usati (1-30 coprono la maggior
# parte dei progetti creati con Home+Project). Gli scenari vengono comunque
# creati/gestiti nell'app installatore: qui li rendiamo solo richiamabili.
SCENARIO_ADDRESS_RANGE = range(1, 31)

# Timeout di scansione bus in secondi durante l'autodetect
SCAN_TIMEOUT = 30

# Chiave per lo storage delle entita' scoperte
STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}_devices"
