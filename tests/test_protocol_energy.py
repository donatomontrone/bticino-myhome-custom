"""Tests for the conservative WHO=18 active-power protocol surface."""
from custom_components.bticino_myhome.protocol.energy import (
    decode_active_power,
    is_energy_meter_where,
)


def test_documented_energy_meter_where_range() -> None:
    assert is_energy_meter_where("51")
    assert is_energy_meter_where("5255")
    assert not is_energy_meter_where("50")
    assert not is_energy_meter_where("5256")
    assert not is_energy_meter_where("71#0")
    assert not is_energy_meter_where("11")


def test_decode_active_power_in_watts() -> None:
    assert decode_active_power(("0",)) == 0
    assert decode_active_power(("487",)) == 487
    assert decode_active_power(("-25",)) == -25


def test_decode_active_power_rejects_ambiguous_payloads() -> None:
    assert decode_active_power(()) is None
    assert decode_active_power(("12.5",)) is None
    assert decode_active_power(("invalid",)) is None
    assert decode_active_power(("100", "extra")) is None
