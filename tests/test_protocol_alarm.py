"""Deterministic tests for OpenWebNet WHO=5 burglar-alarm semantics."""
from __future__ import annotations

import pytest

from custom_components.bticino_myhome.protocol import normalize_frame, parse_frame
from custom_components.bticino_myhome.protocol.alarm import (
    alarm_arm_all,
    alarm_arm_partitions,
    alarm_disarm_all,
    alarm_partition_activate,
    alarm_partition_partialize,
    alarm_partition_status_request,
    alarm_system_status_request,
    partition_from_where,
)


def test_alarm_command_builders_match_documented_legacy_frames() -> None:
    assert alarm_arm_all() == "*5*8##"
    assert alarm_disarm_all() == "*5*9##"
    assert alarm_arm_partitions([6, 1, 2, 5, 2]) == "*5*8#1256##"
    assert alarm_partition_activate(3) == "*5*11*#3##"
    assert alarm_partition_partialize(3) == "*5*18*#3##"


def test_alarm_status_request_builders_match_who5_specification() -> None:
    assert alarm_system_status_request() == "*#5*0##"
    assert alarm_partition_status_request(1) == "*#5*#1##"
    assert alarm_partition_status_request(8) == "*#5*#8##"


def test_alarm_partition_validation_is_conservative() -> None:
    with pytest.raises(ValueError):
        alarm_arm_partitions([])
    with pytest.raises(ValueError):
        alarm_arm_partitions([0])
    with pytest.raises(ValueError):
        alarm_partition_status_request(9)


def test_alarm_system_events_with_empty_where_are_parsed_as_central() -> None:
    armed = parse_frame("*5*8**##")
    disarmed = parse_frame("*5*9**##")
    assert armed is not None
    assert disarmed is not None
    assert armed.where == "0"
    assert normalize_frame(armed).state == "armed_away"
    assert normalize_frame(disarmed).state == "disarmed"


def test_alarm_partition_events_keep_parameterized_where() -> None:
    active = parse_frame("*5*11*#2##")
    partialized = parse_frame("*5*18*#2##")
    assert active is not None
    assert partialized is not None
    assert active.where == "#2"
    assert partition_from_where(active.where) == 2
    assert normalize_frame(active).state is None


def test_alarm_events_use_official_what_meaning_not_old_placeholders() -> None:
    maintenance = parse_frame("*5*0**##")
    battery_fault = parse_frame("*5*4**##")
    intrusion = parse_frame("*5*15*#2##")
    assert maintenance is not None
    assert battery_fault is not None
    assert intrusion is not None
    assert normalize_frame(maintenance).state is None
    assert normalize_frame(battery_fault).state is None
    assert normalize_frame(intrusion).state == "triggered"
