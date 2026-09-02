"""OpenWebNet command builders.

The builders deliberately return strings because OWNd 0.7.49 accepts raw
OpenWebNet messages. Keeping construction here prevents HA entities and
Discovery from having to know protocol syntax.
"""
from __future__ import annotations


def build_command(who: str, what: str, where: str) -> str:
    """Build a standard OpenWebNet command/event frame."""
    return f"*{who}*{what}*{where}##"


def build_status_request(who: str, where: str) -> str:
    """Build the OpenWebNet status request used by conservative discovery."""
    return f"*#{who}*{where}##"


def light_on(where: str) -> str:
    return build_command("1", "1", where)


def light_off(where: str) -> str:
    return build_command("1", "0", where)


def cover_open(where: str) -> str:
    return build_command("2", "1", where)


def cover_close(where: str) -> str:
    return build_command("2", "2", where)


def cover_stop(where: str) -> str:
    return build_command("2", "0", where)


def load_on(where: str) -> str:
    return build_command("3", "1", where)


def load_off(where: str) -> str:
    return build_command("3", "0", where)


def alarm_arm_away(where: str) -> str:
    return build_command("5", "1", where)


def alarm_arm_home(where: str) -> str:
    return build_command("5", "3", where)


def alarm_disarm(where: str) -> str:
    return build_command("5", "0", where)


def scene_activate(where: str) -> str:
    return build_command("0", "1", where)


def door_lock_release(where: str) -> str:
    return build_command("7", "10", where)
