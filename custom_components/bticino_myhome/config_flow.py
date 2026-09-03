"""BTicino MyHome configuration and options flows."""
from __future__ import annotations

import logging
from dataclasses import replace
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, ConfigFlowResult
from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

if TYPE_CHECKING:
    from homeassistant.helpers.service_info.ssdp import SsdpServiceInfo

from .const import (
    CONF_DEVICES,
    CONF_GATEWAY_FIRMWARE,
    CONF_GATEWAY_HOST,
    CONF_GATEWAY_ID,
    CONF_GATEWAY_MANUFACTURER,
    CONF_GATEWAY_MODEL,
    CONF_GATEWAY_PASSWORD,
    CONF_GATEWAY_PORT,
    CONF_GATEWAY_SERIAL,
    CONF_GATEWAY_UDN,
    DEFAULT_PORT,
    DOMAIN,
)
from .discovery import BticinoDiscovery, DiscoveredDevice, DiscoveredGateway
from .gateway import (
    BticinoGateway,
    BticinoGatewayAuthError,
    BticinoGatewayError,
)
from .protocol.thermoregulation import (
    CLIMATE_PROFILE_COOLING,
    CLIMATE_PROFILE_HEATING,
    CLIMATE_PROFILE_HEATING_COOLING,
)

_LOGGER = logging.getLogger(__name__)
_CONF_CLEAR_PASSWORD = "clear_password"
_CONF_CLIMATE_PROFILE = "climate_profile"


class BticinoMyHomeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 3

    def __init__(self) -> None:
        self._ssdp_gateway: DiscoveredGateway | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = str(user_input[CONF_GATEWAY_HOST]).strip()
            port = int(user_input[CONF_GATEWAY_PORT])
            password = str(user_input.get(CONF_GATEWAY_PASSWORD, ""))
            discovered = await BticinoDiscovery.discover_gateway(host, timeout=3)
            gateway_info = (
                replace(discovered, port=port)
                if discovered is not None
                else DiscoveredGateway(host=host, port=port)
            )
            if result := self._handle_existing_gateway(gateway_info):
                return result
            await self.async_set_unique_id(gateway_info.identity)
            self._abort_if_unique_id_configured()
            try:
                await self._async_test_gateway(gateway_info, password)
            except BticinoGatewayAuthError as err:
                _LOGGER.warning(
                    "Authentication rejected by BTicino gateway %s:%s: %s",
                    host,
                    port,
                    err,
                )
                errors["base"] = "invalid_auth"
            except BticinoGatewayError as err:
                _LOGGER.warning(
                    "Unable to connect to BTicino gateway %s:%s: %s",
                    host,
                    port,
                    err,
                )
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=self._entry_title(gateway_info),
                    data=self._entry_data(gateway_info, password),
                )
        return self.async_show_form(
            step_id="user",
            data_schema=_gateway_form_schema(),
            errors=errors,
        )

    async def async_step_ssdp(
        self, discovery_info: SsdpServiceInfo
    ) -> ConfigFlowResult:
        host = urlparse(discovery_info.ssdp_location or "").hostname
        if not host:
            return self.async_abort(reason="cannot_connect")
        upnp = discovery_info.upnp
        ssdp_gateway = DiscoveredGateway(
            host=host,
            port=DEFAULT_PORT,
            serial=_optional_text(upnp.get("serialNumber")),
            udn=_optional_text(
                upnp.get("UDN")
                or discovery_info.ssdp_udn
                or discovery_info.ssdp_usn
            ),
            model=_optional_text(upnp.get("modelName")),
            firmware=_optional_text(upnp.get("modelNumber")),
            manufacturer=_optional_text(upnp.get("manufacturer")),
        )
        enriched = await BticinoDiscovery.discover_gateway(host, timeout=3)
        if enriched is not None:
            ssdp_gateway = _merge_gateway_info(ssdp_gateway, enriched)
        if result := self._handle_existing_gateway(ssdp_gateway):
            return result
        await self.async_set_unique_id(ssdp_gateway.identity)
        self._abort_if_unique_id_configured()
        self._ssdp_gateway = ssdp_gateway
        self.context["title_placeholders"] = {
            "name": ssdp_gateway.model or "MH201",
            "host": ssdp_gateway.host,
        }
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        gateway_info = self._ssdp_gateway
        if gateway_info is None:
            return self.async_abort(reason="cannot_connect")
        errors: dict[str, str] = {}
        if user_input is not None:
            port = int(user_input[CONF_GATEWAY_PORT])
            password = str(user_input.get(CONF_GATEWAY_PASSWORD, ""))
            gateway_info = replace(gateway_info, port=port)
            self._ssdp_gateway = gateway_info
            try:
                await self._async_test_gateway(gateway_info, password)
            except BticinoGatewayAuthError as err:
                _LOGGER.warning(
                    "Authentication rejected by discovered BTicino gateway %s:%s: %s",
                    gateway_info.host,
                    port,
                    err,
                )
                errors["base"] = "invalid_auth"
            except BticinoGatewayError as err:
                _LOGGER.warning(
                    "Unable to connect to discovered BTicino gateway %s:%s: %s",
                    gateway_info.host,
                    port,
                    err,
                )
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=self._entry_title(gateway_info),
                    data=self._entry_data(gateway_info, password),
                )
        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_GATEWAY_PORT, default=gateway_info.port
                    ): _number_selector(1, 65535),
                    vol.Optional(CONF_GATEWAY_PASSWORD, default=""): _password_selector(),
                }
            ),
            errors=errors,
            description_placeholders={
                "host": gateway_info.host,
                "model": gateway_info.model or "MH201",
            },
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            password = str(user_input.get(CONF_GATEWAY_PASSWORD, ""))
            gateway_info = _gateway_from_entry(entry)
            try:
                await self._async_test_gateway(gateway_info, password)
            except BticinoGatewayAuthError:
                errors["base"] = "invalid_auth"
            except BticinoGatewayError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={CONF_GATEWAY_PASSWORD: password},
                )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_GATEWAY_PASSWORD, default=""
                    ): _password_selector()
                }
            ),
            errors=errors,
            description_placeholders={
                "host": str(entry.data[CONF_GATEWAY_HOST])
            },
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            host = str(user_input[CONF_GATEWAY_HOST]).strip()
            port = int(user_input[CONF_GATEWAY_PORT])
            password = _resolve_reconfigure_password(entry, user_input)
            discovered = await BticinoDiscovery.discover_gateway(host, timeout=3)
            candidate = (
                replace(discovered, port=port)
                if discovered is not None
                else DiscoveredGateway(host=host, port=port)
            )
            if _gateway_identity_conflicts(entry, candidate):
                errors["base"] = "wrong_gateway"
            elif self._identity_owned_by_other_entry(entry, candidate):
                errors["base"] = "already_configured"
            else:
                gateway_info = _gateway_with_entry_metadata(entry, candidate)
                try:
                    await self._async_test_gateway(gateway_info, password)
                except BticinoGatewayAuthError:
                    errors["base"] = "invalid_auth"
                except BticinoGatewayError:
                    errors["base"] = "cannot_connect"
                else:
                    legacy_id = str(
                        entry.data.get(CONF_GATEWAY_ID)
                        or entry.unique_id
                        or f"{entry.data[CONF_GATEWAY_HOST]}:{entry.data[CONF_GATEWAY_PORT]}"
                    )
                    updated_data = {
                        **entry.data,
                        **self._gateway_metadata(gateway_info),
                        CONF_GATEWAY_HOST: gateway_info.host,
                        CONF_GATEWAY_PORT: gateway_info.port,
                        CONF_GATEWAY_PASSWORD: password,
                        CONF_GATEWAY_ID: legacy_id,
                    }
                    unique_id = (
                        gateway_info.identity
                        if gateway_info.serial or gateway_info.udn
                        else entry.unique_id
                    )
                    return self.async_update_reload_and_abort(
                        entry,
                        data=updated_data,
                        unique_id=unique_id,
                        title=self._entry_title(gateway_info),
                    )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_gateway_form_schema(
                host=str(entry.data[CONF_GATEWAY_HOST]),
                port=int(entry.data.get(CONF_GATEWAY_PORT, DEFAULT_PORT)),
                password="",
                allow_clear_password=True,
            ),
            errors=errors,
        )

    async def _async_test_gateway(
        self, gateway_info: DiscoveredGateway, password: str
    ) -> None:
        gateway = BticinoGateway(
            gateway_info.host,
            gateway_info.port,
            password,
            identity=gateway_info.identity,
        )
        await gateway.async_test_connection()

    def _handle_existing_gateway(
        self, gateway_info: DiscoveredGateway
    ) -> ConfigFlowResult | None:
        for entry in self._async_current_entries():
            same_identity = entry.unique_id == gateway_info.identity
            same_endpoint = (
                str(entry.data.get(CONF_GATEWAY_HOST, "")).strip().lower()
                == gateway_info.host.strip().lower()
                and int(entry.data.get(CONF_GATEWAY_PORT, DEFAULT_PORT))
                == gateway_info.port
            )
            if not same_identity and not same_endpoint:
                continue
            legacy_id = str(
                entry.data.get(CONF_GATEWAY_ID)
                or entry.unique_id
                or f"{entry.data[CONF_GATEWAY_HOST]}:{entry.data[CONF_GATEWAY_PORT]}"
            )
            new_data = {
                **entry.data,
                **self._gateway_metadata(gateway_info),
                CONF_GATEWAY_HOST: gateway_info.host,
                CONF_GATEWAY_PORT: gateway_info.port,
                CONF_GATEWAY_ID: legacy_id,
            }
            new_unique_id = (
                gateway_info.identity
                if gateway_info.serial or gateway_info.udn
                else entry.unique_id
            )
            self.hass.config_entries.async_update_entry(
                entry, data=new_data, unique_id=new_unique_id
            )
            return self.async_abort(reason="already_configured")
        return None

    def _identity_owned_by_other_entry(
        self, entry: ConfigEntry, gateway_info: DiscoveredGateway
    ) -> bool:
        if not gateway_info.serial and not gateway_info.udn:
            return False
        identity = gateway_info.identity
        return any(
            other.entry_id != entry.entry_id and other.unique_id == identity
            for other in self._async_current_entries()
        )

    @staticmethod
    def _gateway_metadata(
        gateway_info: DiscoveredGateway,
    ) -> dict[str, Any]:
        metadata: dict[str, Any] = {}
        if gateway_info.serial:
            metadata[CONF_GATEWAY_SERIAL] = gateway_info.serial
        if gateway_info.udn:
            metadata[CONF_GATEWAY_UDN] = gateway_info.udn
        if gateway_info.model:
            metadata[CONF_GATEWAY_MODEL] = gateway_info.model
        if gateway_info.firmware:
            metadata[CONF_GATEWAY_FIRMWARE] = gateway_info.firmware
        if gateway_info.manufacturer:
            metadata[CONF_GATEWAY_MANUFACTURER] = gateway_info.manufacturer
        return metadata

    @classmethod
    def _entry_data(
        cls, gateway_info: DiscoveredGateway, password: str
    ) -> dict[str, Any]:
        return {
            CONF_GATEWAY_HOST: gateway_info.host,
            CONF_GATEWAY_PORT: gateway_info.port,
            CONF_GATEWAY_PASSWORD: password,
            CONF_GATEWAY_ID: gateway_info.identity,
            CONF_DEVICES: [],
            **cls._gateway_metadata(gateway_info),
        }

    @staticmethod
    def _entry_title(gateway_info: DiscoveredGateway) -> str:
        return f"BTicino {gateway_info.model or 'MyHome'} ({gateway_info.host})"

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return BticinoMyHomeOptionsFlow()


class BticinoMyHomeOptionsFlow(config_entries.OptionsFlow):
    def __init__(self) -> None:
        self._passive_found: list[DiscoveredDevice] = []

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            action = user_input.get("action", "none")
            if action == "scan":
                return await self.async_step_run_discovery(user_input)
            if action == "learn":
                return await self.async_step_passive_learning()
            if action == "manual":
                return await self.async_step_manual_device()
            if action == "remove":
                return await self.async_step_remove_device()
            return self.async_create_entry(title="", data={})
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional("action", default="none"): SelectSelector(
                        SelectSelectorConfig(
                            options=["none", "scan", "learn", "manual", "remove"],
                            translation_key="options_action",
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional(
                        "include_scenarios", default=False
                    ): BooleanSelector(),
                    vol.Optional(
                        "discovery_listen_seconds", default=3
                    ): _number_selector(0, 60),
                }
            ),
        )

    async def async_step_passive_learning(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is None:
            return self.async_show_form(
                step_id="passive_learning",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            "listen_seconds", default=20
                        ): _number_selector(5, 120)
                    }
                ),
            )
        runtime = self.config_entry.runtime_data
        if runtime is None:
            return self.async_abort(reason="cannot_connect")
        try:
            found = await BticinoDiscovery(runtime.gateway).async_passive_listen(
                int(user_input["listen_seconds"])
            )
        except BticinoGatewayError as err:
            _LOGGER.warning("Passive BTicino learning failed: %s", err)
            return self.async_abort(reason="cannot_connect")
        except Exception as err:
            _LOGGER.exception("Unexpected passive BTicino learning failure: %s", err)
            return self.async_abort(reason="cannot_connect")
        if not found:
            return self.async_abort(reason="no_devices_found")
        self._passive_found = found
        return await self.async_step_select_learned()

    async def async_step_select_learned(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            selected = set(user_input.get("devices", []))
            runtime = self.config_entry.runtime_data
            if runtime is None:
                return self.async_abort(reason="cannot_connect")
            for device in self._passive_found:
                if device.key in selected:
                    runtime.device_manager.add(device)
            self._persist_devices(runtime.device_manager.as_dicts())
            return self.async_create_entry(title="", data={})
        options = {
            device.key: f"{device.name} — WHO={device.who}, WHERE={device.where}"
            for device in self._passive_found
        }
        return self.async_show_form(
            step_id="select_learned",
            data_schema=vol.Schema(
                {
                    vol.Required("devices", default=list(options)): _device_selector(
                        options
                    )
                }
            ),
        )

    async def async_step_run_discovery(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        user_input = user_input or {}
        runtime = self.config_entry.runtime_data
        if runtime is None:
            return self.async_abort(reason="cannot_connect")
        try:
            found = await BticinoDiscovery(runtime.gateway).async_run_full_scan(
                include_scenarios=bool(user_input.get("include_scenarios", False)),
                listen_seconds=int(user_input.get("discovery_listen_seconds", 3)),
            )
        except BticinoGatewayError as err:
            _LOGGER.warning("BTicino discovery failed: %s", err)
            return self.async_abort(reason="cannot_connect")
        except Exception as err:
            _LOGGER.exception("Unexpected BTicino discovery failure: %s", err)
            return self.async_abort(reason="cannot_connect")
        if not found:
            return self.async_abort(reason="no_devices_found")
        for device in found:
            runtime.device_manager.add(device)
        self._persist_devices(runtime.device_manager.as_dicts())
        return self.async_create_entry(title="", data={})

    async def async_step_manual_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            runtime = self.config_entry.runtime_data
            if runtime is None:
                return self.async_abort(reason="cannot_connect")
            climate_profile = user_input.get(_CONF_CLIMATE_PROFILE)
            try:
                device = BticinoDiscovery.from_manual(
                    who=str(user_input["who"]),
                    where=str(user_input["where"]),
                    device_type=str(user_input["device_type"]),
                    name=str(user_input.get("name", "")) or None,
                    climate_profile=(
                        str(climate_profile) if climate_profile is not None else None
                    ),
                )
            except ValueError:
                errors["base"] = "invalid_device"
            else:
                runtime.device_manager.add(device)
                self._persist_devices(runtime.device_manager.as_dicts())
                return self.async_create_entry(title="", data={})
        return self.async_show_form(
            step_id="manual_device",
            data_schema=vol.Schema(
                {
                    vol.Required("who"): TextSelector(),
                    vol.Required("where"): TextSelector(),
                    vol.Required("device_type"): SelectSelector(
                        SelectSelectorConfig(
                            options=[
                                "scene",
                                "light",
                                "cover",
                                "load",
                                "climate",
                                "alarm",
                                "intercom",
                                "door_lock",
                                "energy",
                            ],
                            translation_key="device_type",
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional(_CONF_CLIMATE_PROFILE): SelectSelector(
                        SelectSelectorConfig(
                            options=[
                                CLIMATE_PROFILE_HEATING,
                                CLIMATE_PROFILE_COOLING,
                                CLIMATE_PROFILE_HEATING_COOLING,
                            ],
                            translation_key="climate_profile",
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional("name", default=""): TextSelector(),
                }
            ),
            errors=errors,
        )

    async def async_step_remove_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        runtime = self.config_entry.runtime_data
        if runtime is None:
            return self.async_abort(reason="cannot_connect")

        devices = runtime.device_manager.devices
        if not devices:
            return self.async_abort(reason="no_devices_configured")

        options = {
            device.key: f"{device.name} — WHO={device.who}, WHERE={device.where}"
            for device in devices
        }
        if user_input is not None:
            selected = set(user_input.get("devices", []))
            for device in tuple(devices):
                if device.key not in selected:
                    continue
                if runtime.device_manager.remove(device.key):
                    self._remove_device_registry_entry(device)
            self._persist_devices(runtime.device_manager.as_dicts())
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="remove_device",
            data_schema=vol.Schema(
                {
                    vol.Required("devices", default=[]): _device_selector(options)
                }
            ),
        )

    def _remove_device_registry_entry(self, device: DiscoveredDevice) -> None:
        runtime = self.config_entry.runtime_data
        registry = dr.async_get(self.hass)
        device_entry = registry.async_get_device(
            identifiers={
                (
                    DOMAIN,
                    f"{runtime.gateway.identity}:{device.who}:{device.where}",
                )
            }
        )
        if device_entry is not None:
            registry.async_remove_device(device_entry.id)

    def _persist_devices(self, devices: list[dict[str, Any]]) -> None:
        entry = self.config_entry
        self.hass.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_DEVICES: devices}
        )


def _gateway_form_schema(
    *,
    host: str | None = None,
    port: int = DEFAULT_PORT,
    password: str = "",
    allow_clear_password: bool = False,
) -> vol.Schema:
    host_marker = vol.Required(CONF_GATEWAY_HOST)
    if host is not None:
        host_marker = vol.Required(CONF_GATEWAY_HOST, default=host)
    schema: dict[vol.Marker, Any] = {
        host_marker: TextSelector(),
        vol.Required(CONF_GATEWAY_PORT, default=port): _number_selector(1, 65535),
        vol.Optional(CONF_GATEWAY_PASSWORD, default=password): _password_selector(),
    }
    if allow_clear_password:
        schema[vol.Optional(_CONF_CLEAR_PASSWORD, default=False)] = BooleanSelector()
    return vol.Schema(schema)


def _number_selector(minimum: float, maximum: float) -> NumberSelector:
    return NumberSelector(
        NumberSelectorConfig(
            min=minimum,
            max=maximum,
            step=1,
            mode=NumberSelectorMode.BOX,
        )
    )


def _password_selector() -> TextSelector:
    return TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))


def _device_selector(options: dict[str, str]) -> SelectSelector:
    selector_options: list[SelectOptionDict] = [
        {"value": key, "label": label} for key, label in options.items()
    ]
    return SelectSelector(
        SelectSelectorConfig(
            options=selector_options,
            multiple=True,
            mode=SelectSelectorMode.LIST,
        )
    )


def _resolve_reconfigure_password(
    entry: ConfigEntry, user_input: dict[str, Any]
) -> str:
    if bool(user_input.get(_CONF_CLEAR_PASSWORD, False)):
        return ""
    password_input = str(user_input.get(CONF_GATEWAY_PASSWORD, ""))
    return password_input or str(entry.data.get(CONF_GATEWAY_PASSWORD, ""))


def _gateway_from_entry(entry: ConfigEntry) -> DiscoveredGateway:
    return DiscoveredGateway(
        host=str(entry.data[CONF_GATEWAY_HOST]),
        port=int(entry.data.get(CONF_GATEWAY_PORT, DEFAULT_PORT)),
        serial=_optional_text(entry.data.get(CONF_GATEWAY_SERIAL)),
        udn=_optional_text(entry.data.get(CONF_GATEWAY_UDN)),
        model=_optional_text(entry.data.get(CONF_GATEWAY_MODEL)),
        firmware=_optional_text(entry.data.get(CONF_GATEWAY_FIRMWARE)),
        manufacturer=_optional_text(entry.data.get(CONF_GATEWAY_MANUFACTURER)),
    )


def _gateway_with_entry_metadata(
    entry: ConfigEntry, gateway_info: DiscoveredGateway
) -> DiscoveredGateway:
    current = _gateway_from_entry(entry)
    return DiscoveredGateway(
        host=gateway_info.host,
        port=gateway_info.port,
        serial=gateway_info.serial or current.serial,
        udn=gateway_info.udn or current.udn,
        model=gateway_info.model or current.model,
        firmware=gateway_info.firmware or current.firmware,
        manufacturer=gateway_info.manufacturer or current.manufacturer,
    )


def _gateway_identity_conflicts(
    entry: ConfigEntry, gateway_info: DiscoveredGateway
) -> bool:
    entry_serial = _optional_text(entry.data.get(CONF_GATEWAY_SERIAL))
    entry_udn = _optional_text(entry.data.get(CONF_GATEWAY_UDN))
    if (
        entry_serial
        and gateway_info.serial
        and entry_serial.casefold() != gateway_info.serial.casefold()
    ):
        return True
    if (
        entry_udn
        and gateway_info.udn
        and entry_udn.casefold() != gateway_info.udn.casefold()
    ):
        return True
    unique_id = (entry.unique_id or "").casefold()
    if (
        unique_id.startswith("serial:")
        and gateway_info.serial
        and unique_id != f"serial:{gateway_info.serial.casefold()}"
    ):
        return True
    return bool(
        unique_id.startswith("udn:")
        and gateway_info.udn
        and unique_id != f"udn:{gateway_info.udn.casefold()}"
    )


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _merge_gateway_info(
    primary: DiscoveredGateway, secondary: DiscoveredGateway
) -> DiscoveredGateway:
    return DiscoveredGateway(
        host=primary.host,
        port=secondary.port or primary.port,
        serial=primary.serial or secondary.serial,
        udn=primary.udn or secondary.udn,
        model=primary.model or secondary.model,
        firmware=primary.firmware or secondary.firmware,
        manufacturer=primary.manufacturer or secondary.manufacturer,
    )
