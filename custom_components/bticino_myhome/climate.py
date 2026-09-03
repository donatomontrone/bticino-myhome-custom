"""Climate platform for BTicino MyHome WHO=4."""
from __future__ import annotations

from typing import Any, ClassVar

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import BticinoEntity
from .gateway import BticinoGatewayError
from .protocol import (
    NormalizedEvent,
    build_command,
    build_dimension_request,
    build_dimension_write,
)

MIN_TEMP = 5.0
MAX_TEMP = 40.0
PRESET_ECO = "eco"

_MODE_TO_WHAT = {
    HVACMode.OFF: "303",
    HVACMode.HEAT: "110",
    HVACMode.COOL: "210",
    HVACMode.AUTO: "311",
}
_PROBE_MODE = {
    "0": "cool",
    "1": "heat",
    "102": "eco",
    "202": "eco",
    "302": "eco",
    "103": "off",
    "203": "off",
    "303": "off",
    "110": "heat",
    "210": "cool",
    "310": "auto",
    "111": "auto",
    "211": "auto",
    "311": "auto",
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    runtime = entry.runtime_data
    gateway = runtime.gateway
    manager = runtime.device_manager
    known = {device.key for device in manager.devices if device.device_type == "climate"}
    async_add_entities(
        [
            BticinoClimate(gateway, device.who, device.where, device.name)
            for device in manager.devices
            if device.device_type == "climate"
        ]
    )

    def _device_added(device) -> None:
        if device.device_type != "climate" or device.key in known:
            return
        known.add(device.key)
        async_add_entities([BticinoClimate(gateway, device.who, device.where, device.name)])

    entry.async_on_unload(manager.add_listener(_device_added))


class BticinoClimate(BticinoEntity, ClimateEntity):
    """Thermoregulation endpoint exposed as a Home Assistant climate entity."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes: ClassVar[list[HVACMode]] = [
        HVACMode.OFF,
        HVACMode.HEAT,
        HVACMode.COOL,
        HVACMode.AUTO,
    ]
    _attr_preset_modes: ClassVar[list[str]] = [PRESET_ECO]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
    )
    _attr_target_temperature_step = 0.5
    _attr_min_temp = MIN_TEMP
    _attr_max_temp = MAX_TEMP

    def __init__(self, gateway, who: str, where: str, name: str) -> None:
        super().__init__(gateway, who, where, name)
        self._attr_hvac_mode = HVACMode.OFF
        self._attr_hvac_action = HVACAction.OFF
        self._attr_preset_mode = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        for dimension in ("0", "14", "12"):
            try:
                await self.gateway.async_send(
                    build_dimension_request("4", self.where, dimension),
                    is_status_request=True,
                )
            except BticinoGatewayError:
                # Initial state is best-effort; the persistent event session can
                # still populate the entity when bus traffic arrives.
                continue

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        what = _MODE_TO_WHAT.get(hvac_mode)
        if what is None:
            raise ValueError(f"Unsupported HVAC mode: {hvac_mode}")
        await self.gateway.async_send(build_command("4", what, self.where))
        self._attr_hvac_mode = hvac_mode
        self._attr_preset_mode = None
        self._attr_hvac_action = HVACAction.OFF if hvac_mode == HVACMode.OFF else HVACAction.IDLE
        self._write_state()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if preset_mode != PRESET_ECO:
            raise ValueError(f"Unsupported preset mode: {preset_mode}")
        if self.hvac_mode == HVACMode.COOL:
            what = "202"
        elif self.hvac_mode == HVACMode.AUTO:
            what = "302"
        else:
            what = "102"
        await self.gateway.async_send(build_command("4", what, self.where))
        self._attr_preset_mode = PRESET_ECO
        self._attr_hvac_action = HVACAction.IDLE
        self._write_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temperature = kwargs.get("temperature")
        if temperature is None:
            return
        value = float(temperature)
        if not MIN_TEMP <= value <= MAX_TEMP:
            raise ValueError(f"Temperature out of range: {value}")
        encoded = f"{int(round(value * 10)):04d}"
        await self.gateway.async_send(
            build_dimension_write("4", self.where, "14", encoded)
        )
        self._attr_target_temperature = value
        self._write_state()

    def _handle_event(self, event: NormalizedEvent) -> None:
        if event.who != "4" or event.where != self.where:
            return

        if event.dimension == "0" and event.values:
            self._attr_current_temperature = _decode_temperature(event.values[0])
        elif event.dimension == "14" and event.values:
            self._attr_target_temperature = _decode_temperature(event.values[0])
        elif event.dimension == "12" and event.values:
            self._attr_current_temperature = _decode_temperature(event.values[0])
            if len(event.values) > 1:
                self._apply_mode(_PROBE_MODE.get(event.values[1]), event.values[1])
        elif event.dimension == "19" and len(event.values) >= 2:
            cooling = _as_int(event.values[0])
            heating = _as_int(event.values[1])
            if heating > 0:
                self._attr_hvac_action = HVACAction.HEATING
            elif cooling > 0:
                self._attr_hvac_action = HVACAction.COOLING
            elif self.hvac_mode == HVACMode.OFF:
                self._attr_hvac_action = HVACAction.OFF
            else:
                self._attr_hvac_action = HVACAction.IDLE
        elif event.state is not None:
            self._apply_mode(event.state, event.what)
        else:
            return
        self._write_state()

    def _apply_mode(self, state: str | None, what: str | None) -> None:
        if state == "off":
            self._attr_hvac_mode = HVACMode.OFF
            self._attr_preset_mode = None
            self._attr_hvac_action = HVACAction.OFF
        elif state == "heat":
            self._attr_hvac_mode = HVACMode.HEAT
            self._attr_preset_mode = None
            self._attr_hvac_action = HVACAction.IDLE
        elif state == "cool":
            self._attr_hvac_mode = HVACMode.COOL
            self._attr_preset_mode = None
            self._attr_hvac_action = HVACAction.IDLE
        elif state == "auto":
            self._attr_hvac_mode = HVACMode.AUTO
            self._attr_preset_mode = None
            self._attr_hvac_action = HVACAction.IDLE
        elif state == "eco":
            self._attr_preset_mode = PRESET_ECO
            if what == "202":
                self._attr_hvac_mode = HVACMode.COOL
            elif what == "302":
                self._attr_hvac_mode = HVACMode.AUTO
            else:
                self._attr_hvac_mode = HVACMode.HEAT
            self._attr_hvac_action = HVACAction.IDLE

    def _write_state(self) -> None:
        if self.hass is not None:
            self.async_write_ha_state()


def _decode_temperature(value: str) -> float | None:
    try:
        return int(value) / 10.0
    except (TypeError, ValueError):
        return None


def _as_int(value: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
