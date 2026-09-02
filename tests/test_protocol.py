from custom_components.bticino_myhome.protocol import (
    build_command,
    build_status_request,
    normalize_frame,
    parse_frame,
)
from custom_components.bticino_myhome.protocol.commands import (
    alarm_arm_away,
    cover_open,
    light_off,
    light_on,
    load_off,
    load_on,
    scene_activate,
    door_lock_release,
)


def test_parse_standard_frame() -> None:
    frame = parse_frame("*1*1*21##")
    assert frame is not None
    assert frame.who == "1"
    assert frame.what == "1"
    assert frame.where == "21"
    assert frame.key == "1-21"


def test_parser_rejects_status_request() -> None:
    assert parse_frame("*#1*21##") is None


def test_parser_rejects_diagnostic_status_frames() -> None:
    # Diagnostic/status frames are not normalized events until their semantics
    # are verified against real MH201 captures.
    assert parse_frame("*#1001*21##") is None
    assert parse_frame("*#1004*21##") is None


def test_normalizer_maps_light_state() -> None:
    frame = parse_frame("*1*0*21##")
    assert frame is not None
    event = normalize_frame(frame)
    assert event.device_type == "light"
    assert event.state == "off"


def test_command_builders() -> None:
    assert build_command("1", "1", "21") == "*1*1*21##"
    assert build_status_request("1", "21") == "*#1*21##"
    assert light_on("21") == "*1*1*21##"
    assert light_off("21") == "*1*0*21##"
    assert cover_open("15") == "*2*1*15##"
    assert alarm_arm_away("0") == "*5*1*0##"


def test_public_command_exports():
    assert load_on("7") == "*3*1*7##"
    assert load_off("7") == "*3*0*7##"
    assert scene_activate("4") == "*0*1*4##"
    assert door_lock_release("0") == "*7*10*0##"


def test_parser_rejects_empty_input():
    assert parse_frame("") is None
    assert parse_frame(None) is None
