"""OpenWebNet WHO=18 Energy Management helpers."""
from __future__ import annotations

WHO_ENERGY_MANAGEMENT = "18"
DIM_ACTIVE_POWER = "113"
CAPABILITY_ACTIVE_POWER = "active_power"


def is_energy_meter_where(where: str) -> bool:
    """Return whether WHERE matches the documented 5N energy-meter address."""
    address = str(where).strip()
    if len(address) < 2 or not address.startswith("5"):
        return False
    suffix = address[1:]
    if not suffix.isdigit():
        return False
    meter_number = int(suffix)
    return 1 <= meter_number <= 255


def decode_active_power(values: tuple[str, ...]) -> int | None:
    """Decode a WHO=18 DIM=113 active-power value expressed in watts."""
    if len(values) != 1:
        return None
    try:
        return int(values[0])
    except (TypeError, ValueError):
        return None
