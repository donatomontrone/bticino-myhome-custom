"""Climate platform for BTicino MyHome WHO=4."""
from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .data import BticinoConfigEntry
from .entity import BticinoEntity
from .gateway import BticinoGateway, BticinoGatewayError
from .platform import setup_dynamic_entities
from .protocol import NormalizedEvent, build_dimension_request
from .protocol.thermoregulation import (
    CAPABILITY_COOLING,
    CAPABILITY_HEATING,
    DIM_COMPLETE_PROBE_STATUS,
    DIM_MEASURED_TEMPERATURE,
    DIM_SETPOINT_TEMPERATURE,
    DIM_VALVES_STATUS,
    OPERATION_MODE_CONDITIONING,
    OPERATION_MODE_GENERIC,
    OPERATION_MODE_HEATING,
    STATE_ANTIFREEZE,
    STATE_CONDITIONING,
    STATE_GENERIC_PROTECTION,
    STATE_HEATING,
    STATE_MANUAL_CONDITIONING,
    STATE_MANUAL_GENERIC,
    STATE_MANUAL_HEATING,
    STATE_OFF_CONDITIONING,
    STATE_OFF_GENERIC,
    STATE_OFF_HEATING,
    STATE_PROGRAMMING_CONDITIONING,
    STATE_PROGRAMMING_GENERIC,
    STATE_PROGRAMMING_HEATING,
    STATE_THERMAL_PROTECTION,
    THERMOREGULATION_STATE_MAP,
    build_zone_mode_command,
    build_zone_setpoint_command,
    output_is_active,
)

MIN_TEMP = 5.0
MAX_TEMP = 40.0
PRESET_ANTIFREEZE = "antifreeze"
PRESET_THERMAL_PROTECTION = "thermal_protection"
PRESET_GENERIC_PROTECTION = "generic_protection"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BticinoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    gateway = entry.runtime_data.gateway
    setup_dynamic_entities(
        hass,
        entry,
        async_add_entities,
        matches=lambda device: device.device_type == "climate",
        factory=lambda device: BticinoClimate(
            gateway,
            device.who,
            device.where,
            device.name,
            capabilities=device.capabilities,
        ),
    )


class BticinoClimate(BticinoEntity, ClimateEntity):
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
    )
    _attr_target_temperature_step = 0.5
    _attr_min_temp = MIN_TEMP
    _attr_max_temp = MAX_TEMP

    def __init__(
        self,
        gateway: BticinoGateway,
        who: str,
        where: str,
        name: str,
        *,
        capabilities: tuple[str, ...] = (),
    ) -> None:
        super().__init__(gateway, who, where, name)
        explicit_thermal_profile = bool(
            {CAPABILITY_HEATING, CAPABILITY_COOLING}.intersection(capabilities)
        )
        self._supports_heating = (
            CAPABILITY_HEATING in capabilities or not explicit_thermal_profile
        )
        self._supports_cooling = (
            CAPABILITY_COOLING in capabilities or not explicit_thermal_profile
        )

        self._attr_hvac_modes = [HVACMode.OFF]
        if self._supports_heating:
            self._attr_hvac_modes.append(HVACMode.HEAT)
        if self._supports_cooling:
            self._attr_hvac_modes.append(HVACMode.COOL)
        self._attr_hvac_modes.append(HVACMode.AUTO)

        self._attr_preset_modes = []
        if self._supports_heating:
            self._attr_preset_modes.append(PRESET_ANTIFREEZE)
        if self._supports_cooling:
            self._attr_preset_modes.append(PRESET_THERMAL_PROTECTION)
        if self._supports_heating and self._supports_cooling:
            self._attr_preset_modes.append(PRESET_GENERIC_PROTECTION)

        # Do not fabricate a climate state before OpenWebNet evidence arrives.
        self._attr_hvac_mode = None
        self._attr_hvac_action = None
        self._attr_preset_mode = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.hass is not None:
            task = self.hass.async_create_task(
                self._async_hydrate_climate_state(),
                f"bticino_myhome-climate-state-{self.where}",
            )

            def _cancel_climate_state_task() -> None:
                task.cancel()

            self.async_on_remove(_cancel_climate_state_task)

    async def _async_hydrate_climate_state(self) -> None:
        for dimension in (
            DIM_MEASURED_TEMPERATURE,
            DIM_SETPOINT_TEMPERATURE,
            DIM_COMPLETE_PROBE_STATUS,
        ):
            try:
                await self.gateway.async_send(
                    build_dimension_request("4", self.where, dimension),
                    is_status_request=True,
                )
            except BticinoGatewayError:
                continue

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        what = self._what_for_hvac_mode(hvac_mode)
        await self.gateway.async_send(build_zone_mode_command(self.where, what))

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        what = self._what_for_preset(preset_mode)
        await self.gateway.async_send(build_zone_mode_command(self.where, what))

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temperature = kwargs.get("temperature")
        if temperature is None:
            return
        value = float(temperature)
        if not MIN_TEMP <= value <= MAX_TEMP:
            raise ValueError(f"Temperature out of range: {value}")

        requested_mode = kwargs.get("hvac_mode", self.hvac_mode)
        operation_mode = self._operation_mode_for_setpoint(requested_mode)
        await self.gateway.async_send(
            build_zone_setpoint_command(self.where, value, operation_mode)
        )

    def _what_for_hvac_mode(self, hvac_mode: HVACMode) -> str:
        if hvac_mode == HVACMode.HEAT:
            if not self._supports_heating:
                raise ValueError(f"Unsupported HVAC mode: {hvac_mode}")
            return "110"
        if hvac_mode == HVACMode.COOL:
            if not self._supports_cooling:
                raise ValueError(f"Unsupported HVAC mode: {hvac_mode}")
            return "210"
        if hvac_mode == HVACMode.OFF:
            if self._supports_heating and self._supports_cooling:
                return "303"
            if self._supports_heating:
                return "103"
            return "203"
        if hvac_mode == HVACMode.AUTO:
            if self._supports_heating and self._supports_cooling:
                return "311"
            if self._supports_heating:
                return "111"
            return "211"
        raise ValueError(f"Unsupported HVAC mode: {hvac_mode}")

    def _what_for_preset(self, preset_mode: str) -> str:
        if preset_mode == PRESET_ANTIFREEZE and self._supports_heating:
            return "102"
        if preset_mode == PRESET_THERMAL_PROTECTION and self._supports_cooling:
            return "202"
        if (
            preset_mode == PRESET_GENERIC_PROTECTION
            and self._supports_heating
            and self._supports_cooling
        ):
            return "302"
        raise ValueError(f"Unsupported preset mode: {preset_mode}")

    def _operation_mode_for_setpoint(self, hvac_mode: HVACMode | None) -> str:
        if hvac_mode == HVACMode.HEAT:
            if not self._supports_heating:
                raise ValueError(f"Unsupported HVAC mode: {hvac_mode}")
            return OPERATION_MODE_HEATING
        if hvac_mode == HVACMode.COOL:
            if not self._supports_cooling:
                raise ValueError(f"Unsupported HVAC mode: {hvac_mode}")
            return OPERATION_MODE_CONDITIONING
        if self._supports_heating and not self._supports_cooling:
            return OPERATION_MODE_HEATING
        if self._supports_cooling and not self._supports_heating:
            return OPERATION_MODE_CONDITIONING
        return OPERATION_MODE_GENERIC

    def _handle_event(self, event: NormalizedEvent) -> None:
        if event.who != "4" or event.where.lstrip("#") != self.where.lstrip("#"):
            return
        if event.dimension == DIM_MEASURED_TEMPERATURE and event.values:
            self._attr_current_temperature = _decode_temperature(event.values[0])
        elif event.dimension == DIM_SETPOINT_TEMPERATURE and event.values:
            self._attr_target_temperature = _decode_temperature(event.values[0])
        elif event.dimension == DIM_COMPLETE_PROBE_STATUS and event.values:
            self._attr_current_temperature = _decode_temperature(event.values[0])
            if len(event.values) > 1:
                self._apply_mode(
                    THERMOREGULATION_STATE_MAP.get(event.values[1]), event.values[1]
                )
        elif event.dimension == DIM_VALVES_STATUS and len(event.values) >= 2:
            cooling_active = output_is_active(event.values[0])
            heating_active = output_is_active(event.values[1])
            if heating_active:
                self._attr_hvac_action = HVACAction.HEATING
            elif cooling_active:
                self._attr_hvac_action = HVACAction.COOLING
            elif self.hvac_mode == HVACMode.OFF:
                self._attr_hvac_action = HVACAction.OFF
            elif self.hvac_mode is not None:
                self._attr_hvac_action = HVACAction.IDLE
        elif event.state is not None:
            self._apply_mode(event.state, event.what)
        else:
            return
        self._write_state()

    def _apply_mode(self, state: str | None, what: str | None) -> None:
        del what
        self._attr_preset_mode = None

        if state in {STATE_OFF_HEATING, STATE_OFF_CONDITIONING, STATE_OFF_GENERIC}:
            self._attr_hvac_mode = HVACMode.OFF
            self._attr_hvac_action = HVACAction.OFF
        elif state in {STATE_HEATING, STATE_MANUAL_HEATING}:
            self._attr_hvac_mode = HVACMode.HEAT
            self._attr_hvac_action = HVACAction.IDLE
        elif state in {STATE_CONDITIONING, STATE_MANUAL_CONDITIONING}:
            self._attr_hvac_mode = HVACMode.COOL
            self._attr_hvac_action = HVACAction.IDLE
        elif state in {
            STATE_MANUAL_GENERIC,
            STATE_PROGRAMMING_HEATING,
            STATE_PROGRAMMING_CONDITIONING,
            STATE_PROGRAMMING_GENERIC,
        }:
            self._attr_hvac_mode = HVACMode.AUTO
            self._attr_hvac_action = HVACAction.IDLE
        elif state == STATE_ANTIFREEZE:
            self._attr_hvac_mode = HVACMode.HEAT
            self._attr_preset_mode = PRESET_ANTIFREEZE
            self._attr_hvac_action = HVACAction.IDLE
        elif state == STATE_THERMAL_PROTECTION:
            self._attr_hvac_mode = HVACMode.COOL
            self._attr_preset_mode = PRESET_THERMAL_PROTECTION
            self._attr_hvac_action = HVACAction.IDLE
        elif state == STATE_GENERIC_PROTECTION:
            self._attr_hvac_mode = HVACMode.AUTO
            self._attr_preset_mode = PRESET_GENERIC_PROTECTION
            self._attr_hvac_action = HVACAction.IDLE

    def _write_state(self) -> None:
        if self.hass is not None:
            self.async_write_ha_state()


def _decode_temperature(value: str) -> float | None:
    try:
        return int(value) / 10.0
    except (TypeError, ValueError):
        return None
