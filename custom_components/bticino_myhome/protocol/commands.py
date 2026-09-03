"""OpenWebNet command builders used by entities and discovery."""
from __future__ import annotations


def build_command(who: str, what: str, where: str) -> str:
    return f"*{who}*{what}*{where}##"


def build_status_request(who: str, where: str) -> str:
    return f"*#{who}*{where}##"


def build_dimension_request(who: str, where: str, dimension: str) -> str:
    return f"*#{who}*{where}*{dimension}##"


def build_dimension_write(who: str, where: str, dimension: str, value: str) -> str:
    return f"*#{who}*{where}*#{dimension}*{value}##"


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
