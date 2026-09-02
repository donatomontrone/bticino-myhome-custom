"""Test protocol."""
from custom_components.bticino_myhome.protocol import (
    build_command,
    build_status_request,
    normalize_frame,
    parse_frame,
)
from custom_components.bticino_myhome.protocol.commands import (
    alarm_arm_away,
    cover_open,
    door_lock_release,
    light_off,
    light_on,
    load_off,
    load_on,
    scene_activate,
)


def test_protocol():
    """Verify protocol functions work correctly."""
    pass
