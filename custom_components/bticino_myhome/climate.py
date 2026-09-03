"""Climate platform for BTicino MyHome."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ATTR_TEMPERATURE,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .device import BticinoDevice, BticinoDeviceManager
from .gateway import BticinoGateway

_LOGGER = logging.getLogger(__name__)


# Supported HVAC modes
SUPPORTED_HVAC_MODES = [
    HVACMode.OFF,
    HVACMode.HEAT,
    HVACMode.COOL,
    HVACMode.AUTO,
    HVACMode.ECO,
]

# Supported features
SUPPORTED_FEATURES = (
    ClimateEntityFeature.TARGET_TEMPERATURE
    | ClimateEntityFeature.TURN_OFF
    | ClimateEntityFeature.TURN_ON
)

# Temperature range
MIN_TEMP = 5.0
MAX_TEMP = 40.0


class BticinoClimate(ClimateEntity):
    """Climate entity for BTicino MyHome."""

    _attr_has_entity_name = True
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = SUPPORTED_HVAC_MODES
    _attr_supported_features = SUPPORTED_FEATURES
    _attr_target_temperature_step = 0.5
    _attr_min_temp = MIN_TEMP
    _attr_max_temp = MAX_TEMP

    def __init__(
        self,
        device: BticinoDevice,
        gateway: BticinoGateway,
    ) -> None:
        """Initialize the climate entity."""
        self._device = device
        self._gateway = gateway
        self._attr_unique_id = device.unique_id
        self._attr_device_info = device.device_info
        self._attr_name = device.name

        # State
        self._current_temperature: float | None = None
        self._target_temperature: float | None = None
        self._hvac_mode: HVACMode = HVACMode.OFF
        self._hvac_action: HVACAction = HVACAction.OFF

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self._current_temperature

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        return self._target_temperature

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current HVAC mode."""
        return self._hvac_mode

    @property
    def hvac_action(self) -> HVACAction:
        """Return the current HVAC action."""
        return self._hvac_action

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        # Map HA mode to OpenWebNet WHAT
        what_map = {
            HVACMode.OFF: 303,  # Generic OFF
            HVACMode.HEAT: 110,  # Manual heating
            HVACMode.COOL: 210,  # Manual cooling
            HVACMode.AUTO: 311,  # Program generic
            HVACMode.ECO: 102,  # Antifreeze
        }

        what = what_map.get(hvac_mode)
        if what is None:
            _LOGGER.error("Unsupported HVAC mode: %s", hvac_mode)
            return

        # Send command: *4*WHAT*WHERE##
        where = self._device.where
        frame = f"*4*{what}*{where}##"
        await self._gateway.async_send(frame)

        # Update state
        self._hvac_mode = hvac_mode
        self._hvac_action = _mode_to_action(hvac_mode)
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        # Convert temperature to 4-digit format (e.g., 21.5 -> "0215")
        temp_value = int(temperature * 10)
        temp_str = f"{temp_value:04d}"

        # Send dimension write: *#4*WHERE*#14*TEMP##
        where = self._device.where
        frame = f"*#4*{where}*#14*{temp_str}##"
        await self._gateway.async_send(frame)

        # Update state
        self._target_temperature = temperature
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to Home Assistant."""
        await super().async_added_to_hass()

        # Request initial state
        where = self._device.where

        # Request temperature
        await self._gateway.async_send(f"*#4*{where}*0##", is_status_request=True)

        # Request setpoint
        await self._gateway.async_send(f"*#4*{where}*14##", is_status_request=True)

        # Request mode
        await self._gateway.async_send(f"*#4*{where}*12##", is_status_request=True)

    def update_from_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Update entity state from normalized event."""
        if event_type == "temperature":
            self._current_temperature = data.get("temperature")
        elif event_type == "setpoint":
            self._target_temperature = data.get("setpoint")
        elif event_type == "probe_status":
            self._current_temperature = data.get("temperature")
            mode = data.get("mode")
            if mode:
                self._hvac_mode = _mode_str_to_hvac(mode)
                self._hvac_action = _mode_to_action(self._hvac_mode)
        elif event_type == "mode":
            mode = data.get("mode")
            if mode:
                self._hvac_mode = _mode_str_to_hvac(mode)
                self._hvac_action = _mode_to_action(self._hvac_mode)

        self.async_write_ha_state()


def _mode_str_to_hvac(mode: str) -> HVACMode:
    """Convert mode string to HVACMode."""
    mode_map = {
        "off": HVACMode.OFF,
        "heat": HVACMode.HEAT,
        "cool": HVACMode.COOL,
        "auto": HVACMode.AUTO,
        "eco": HVACMode.ECO,
    }
    return mode_map.get(mode, HVACMode.AUTO)


def _mode_to_action(hvac_mode: HVACMode) -> HVACAction:
    """Convert HVAC mode to HVAC action."""
    action_map = {
        HVACMode.OFF: HVACAction.OFF,
        HVACMode.HEAT: HVACAction.HEATING,
        HVACMode.COOL: HVACAction.COOLING,
        HVACMode.AUTO: HVACAction.HEATING,  # Could be dynamic
        HVACMode.ECO: HVACAction.IDLE,
    }
    return action_map.get(hvac_mode, HVACAction.IDLE)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up climate platform."""
    # Get device manager and gateway
    device_manager: BticinoDeviceManager = hass.data[DOMAIN][entry.entry_id]["device_manager"]
    gateway: BticinoGateway = hass.data[DOMAIN][entry.entry_id]["gateway"]

    # Filter climate devices
    climate_devices = [
        device
        for device in device_manager.devices
        if device.device_type == "climate"
    ]

    # Create entities
    entities = [
        BticinoClimate(device, gateway)
        for device in climate_devices
    ]

    if entities:
        async_add_entities(entities)
