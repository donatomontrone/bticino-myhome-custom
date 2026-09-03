"""OpenWebNet command builders used by entities and discovery."""
from __future__ import annotations


def build_command(who: str, what: str, where: str) -> str:
    return f"*{who}*{what}*{where}##"


def build_status_request(who: str, where: str) -> str:
    return f"*#{who}*{where}##"


def build_dimension_request(who: str, where: str, dimension: str) -> str:
    return f"*#{who}*{where}*{dimension}##"


def build_dimension_write(
    who: str, where: str, dimension: str, value: str, *values: str
) -> str:
    payload = "*".join((str(value), *(str(item) for item in values)))
    return f"*#{who}*{where}*#{dimension}*{payload}##"


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


def scene_activate(where: str) -> str:
    return build_command("0", "1", where)
