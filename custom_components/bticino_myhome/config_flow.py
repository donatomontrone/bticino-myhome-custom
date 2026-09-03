"""BTicino MyHome configuration and options flows."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import CONF_GATEWAY_HOST, CONF_GATEWAY_PASSWORD, CONF_GATEWAY_PORT, DOMAIN
from .discovery import BticinoDiscovery
from .gateway import BticinoGateway, BticinoGatewayError

_LOGGER = logging.getLogger(__name__)


class BticinoMyHomeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle initial BTicino MyHome configuration."""

    VERSION = 2

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Collect gateway connection details and validate them."""
        errors: dict[str, str] = {}
        if user_input is not None:
            host = str(user_input[CONF_GATEWAY_HOST]).strip()
            port = int(user_input[CONF_GATEWAY_PORT])
            password = str(user_input.get(CONF_GATEWAY_PASSWORD, ""))
            await self.async_set_unique_id(f"{host.lower()}:{port}")
            self._abort_if_unique_id_configured()

            gateway = BticinoGateway(host, port, password)
            try:
                await gateway.async_test_connection()
            except BticinoGatewayError as err:
                _LOGGER.warning("Unable to connect to BTicino gateway %s:%s: %s", host, port, err)
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"BTicino MyHome ({host})",
                    data={
                        CONF_GATEWAY_HOST: host,
                        CONF_GATEWAY_PORT: port,
                        CONF_GATEWAY_PASSWORD: password,
                        "devices": [],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_GATEWAY_HOST): str,
                    vol.Required(CONF_GATEWAY_PORT, default=20000): vol.All(
                        vol.Coerce(int), vol.Range(min=1, max=65535)
                    ),
                    vol.Optional(CONF_GATEWAY_PASSWORD, default=""): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return the options flow for an existing entry."""
        return BticinoMyHomeOptionsFlow()


class BticinoMyHomeOptionsFlow(config_entries.OptionsFlow):
    """Options flow for scans and safe passive learning."""

    def __init__(self) -> None:
        self._passive_found = []

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            action = user_input.get("action", "none")
            if action == "scan":
                return await self.async_step_run_discovery(user_input)
            if action == "learn":
                return await self.async_step_passive_learning()
            return self.async_create_entry(title="", data={})
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional("action", default="none"): vol.In(
                        {
                            "none": "Nessuna azione",
                            "scan": "Scansione automatica",
                            "learn": "Impara dispositivi dai pulsanti fisici",
                        }
                    ),
                    vol.Optional("include_scenarios", default=True): bool,
                    vol.Optional("discovery_listen_seconds", default=3): vol.All(
                        vol.Coerce(int), vol.Range(min=0, max=60)
                    ),
                }
            ),
        )

    async def async_step_passive_learning(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is None:
            return self.async_show_form(
                step_id="passive_learning",
                data_schema=vol.Schema(
                    {
                        vol.Required("listen_seconds", default=20): vol.All(
                            vol.Coerce(int), vol.Range(min=5, max=120)
                        ),
                    }
                ),
            )

        entry = self.config_entry
        gateway = BticinoGateway(
            entry.data[CONF_GATEWAY_HOST],
            entry.data[CONF_GATEWAY_PORT],
            entry.data.get(CONF_GATEWAY_PASSWORD, ""),
        )
        try:
            await gateway.async_connect()
            found = await BticinoDiscovery(gateway).async_passive_listen(user_input["listen_seconds"])
        except Exception as err:
            _LOGGER.exception("Passive learning BTicino failed: %s", err)
            found = []
        finally:
            await gateway.async_close()

        if not found:
            return self.async_abort(reason="no_devices_found")
        self._passive_found = found
        return await self.async_step_select_learned()

    async def async_step_select_learned(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            selected = set(user_input.get("devices", []))
            entry = self.config_entry
            manager = entry.runtime_data.device_manager
            for device in self._passive_found:
                if device.key in selected:
                    manager.add(device)

            self.hass.config_entries.async_update_entry(
                entry,
                data={**entry.data, "devices": manager.as_dicts()},
            )
            return self.async_create_entry(title="", data={})

        options = {
            device.key: f"{device.name} — WHO={device.who}, WHERE={device.where}"
            for device in self._passive_found
        }
        return self.async_show_form(
            step_id="select_learned",
            data_schema=vol.Schema(
                {
                    vol.Required("devices", default=list(options)): SelectSelector(
                        SelectSelectorConfig(
                            options=[
                                {"value": key, "label": label}
                                for key, label in options.items()
                            ],
                            multiple=True,
                            mode=SelectSelectorMode.LIST,
                        )
                    )
                }
            ),
        )

    async def async_step_run_discovery(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        user_input = user_input or {}
        entry = self.config_entry
        gateway = BticinoGateway(
            entry.data[CONF_GATEWAY_HOST],
            entry.data[CONF_GATEWAY_PORT],
            entry.data.get(CONF_GATEWAY_PASSWORD, ""),
        )
        try:
            await gateway.async_connect()
            found = await BticinoDiscovery(gateway).async_run_full_scan(
                include_scenarios=user_input.get("include_scenarios", True),
                listen_seconds=user_input.get("discovery_listen_seconds", 3),
            )
        except Exception as err:
            _LOGGER.exception("BTicino discovery failed: %s", err)
            found = []
        finally:
            await gateway.async_close()

        if not found:
            return self.async_abort(reason="no_devices_found")

        manager = entry.runtime_data.device_manager
        for device in found:
            manager.add(device)

        self.hass.config_entries.async_update_entry(
            entry,
            data={**entry.data, "devices": manager.as_dicts()},
        )
        return self.async_create_entry(title="", data={})
