"""Config flow for a local BTicino OpenWebNet gateway."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_GATEWAY_HOST, CONF_GATEWAY_PASSWORD, CONF_GATEWAY_PORT, DEFAULT_PORT, DOMAIN
from .discovery import BticinoDiscovery
from .gateway import BticinoGateway, BticinoGatewayError, async_discover_gateways


class BticinoMyHomeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2

    def __init__(self) -> None:
        self._discovered_gateways: list[dict[str, Any]] = []
        self._chosen_gateway: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        self._discovered_gateways = await async_discover_gateways()
        if self._discovered_gateways:
            return await self.async_step_select_gateway()
        return await self.async_step_manual_gateway()

    async def async_step_select_gateway(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        options = {
            f"{gw['host']}|{gw['port']}": f"{gw.get('model', 'Gateway')} - {gw['host']}"
            for gw in self._discovered_gateways
        }
        options["manual"] = "Inserisci manualmente"
        if user_input is not None:
            choice = user_input["gateway"]
            if choice == "manual":
                return await self.async_step_manual_gateway()
            host, port = choice.split("|", 1)
            self._chosen_gateway = {CONF_GATEWAY_HOST: host, CONF_GATEWAY_PORT: int(port)}
            return await self.async_step_credentials()
        return self.async_show_form(step_id="select_gateway", data_schema=vol.Schema({vol.Required("gateway"): vol.In(options)}))

    async def async_step_manual_gateway(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            self._chosen_gateway = {
                CONF_GATEWAY_HOST: user_input[CONF_GATEWAY_HOST],
                CONF_GATEWAY_PORT: user_input.get(CONF_GATEWAY_PORT, DEFAULT_PORT),
            }
            return await self.async_step_credentials()
        schema = vol.Schema({
            vol.Required(CONF_GATEWAY_HOST): str,
            vol.Optional(CONF_GATEWAY_PORT, default=DEFAULT_PORT): vol.Coerce(int),
        })
        return self.async_show_form(step_id="manual_gateway", data_schema=schema)

    async def async_step_credentials(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            password = user_input.get(CONF_GATEWAY_PASSWORD, "")
            gw = BticinoGateway(self._chosen_gateway[CONF_GATEWAY_HOST], self._chosen_gateway[CONF_GATEWAY_PORT], password)
            try:
                await gw.async_test_connection()
            except BticinoGatewayError:
                errors["base"] = "cannot_connect"
            else:
                # Unique ID is the stable local gateway endpoint unless SSDP provided a serial.
                unique_id = f"{self._chosen_gateway[CONF_GATEWAY_HOST]}:{self._chosen_gateway[CONF_GATEWAY_PORT]}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                devices: list[dict] = []
                try:
                    await gw.async_connect()
                    found = await BticinoDiscovery(gw).async_run_full_scan(listen_seconds=3)
                    devices = [d.to_dict() for d in found]
                except Exception:
                    # Connection has already been validated; a discovery failure must not block setup.
                    devices = []
                finally:
                    await gw.async_close()
                return self.async_create_entry(
                    title=f"BTicino MyHome ({self._chosen_gateway[CONF_GATEWAY_HOST]})",
                    data={
                        CONF_GATEWAY_HOST: self._chosen_gateway[CONF_GATEWAY_HOST],
                        CONF_GATEWAY_PORT: self._chosen_gateway[CONF_GATEWAY_PORT],
                        CONF_GATEWAY_PASSWORD: password,
                        "devices": devices,
                    },
                )
        return self.async_show_form(step_id="credentials", data_schema=vol.Schema({vol.Optional(CONF_GATEWAY_PASSWORD, default=""): str}), errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return BticinoMyHomeOptionsFlow()


class BticinoMyHomeOptionsFlow(config_entries.OptionsFlow):
    """Options flow without storing the ConfigEntry on the flow object."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            if user_input.get("run_discovery"):
                return await self.async_step_run_discovery(user_input)
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional("run_discovery", default=False): bool,
                vol.Optional("include_scenarios", default=True): bool,
                vol.Optional("discovery_listen_seconds", default=3): vol.All(vol.Coerce(int), vol.Range(min=0, max=60)),
            }),
        )

    async def async_step_run_discovery(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        entry = self.config_entry
        gateway = BticinoGateway(
            entry.data[CONF_GATEWAY_HOST], entry.data[CONF_GATEWAY_PORT], entry.data.get(CONF_GATEWAY_PASSWORD, "")
        )
        try:
            await gateway.async_connect()
            found = await BticinoDiscovery(gateway).async_run_full_scan(
                include_scenarios=user_input.get("include_scenarios", True) if user_input else True,
                listen_seconds=user_input.get("discovery_listen_seconds", 3) if user_input else 3,
            )
            self.hass.config_entries.async_update_entry(
                entry, data={**entry.data, "devices": [d.to_dict() for d in found]}
            )
        finally:
            await gateway.async_close()
        return self.async_create_entry(title="", data={k: v for k, v in (user_input or {}).items() if k != "run_discovery"})
