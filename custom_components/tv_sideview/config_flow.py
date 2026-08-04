"""Config flow for Video & TV SideView (Legacy API)."""

from __future__ import annotations

import logging
import re
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from sonyapilib.device import AuthenticationResult, SonyDevice

from .const import (
    CONF_APP_PORT,
    CONF_DMR_PORT,
    CONF_IRCC_PORT,
    CONF_MAC,
    CONF_PIN,
    DEFAULT_APP_PORT,
    DEFAULT_DMR_PORT,
    DEFAULT_IRCC_PORT,
    DEFAULT_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

MAC_RE = re.compile(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")


def _normalize_mac(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    if not MAC_RE.match(value):
        raise vol.Invalid("Invalid MAC address (use AA:BB:CC:DD:EE:FF)")
    return value.upper().replace("-", ":")


def _user_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, "")): str,
            vol.Optional(
                CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)
            ): str,
            vol.Optional(
                CONF_MAC,
                default=defaults.get(CONF_MAC, ""),
                description={
                    "suggested_value": defaults.get(CONF_MAC, ""),
                },
            ): str,
            vol.Optional(
                CONF_APP_PORT,
                default=defaults.get(CONF_APP_PORT, DEFAULT_APP_PORT),
            ): int,
            vol.Optional(
                CONF_DMR_PORT,
                default=defaults.get(CONF_DMR_PORT, DEFAULT_DMR_PORT),
            ): int,
            vol.Optional(
                CONF_IRCC_PORT,
                default=defaults.get(CONF_IRCC_PORT, DEFAULT_IRCC_PORT),
            ): int,
        }
    )


PIN_SCHEMA = vol.Schema({vol.Required(CONF_PIN): str})

MAC_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_MAC, default=""): str,
    }
)


class TVSideViewConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Video & TV SideView (Legacy API)."""

    VERSION = 1

    def __init__(self) -> None:
        self._host: str | None = None
        self._name: str = DEFAULT_NAME
        self._app_port: int = DEFAULT_APP_PORT
        self._dmr_port: int = DEFAULT_DMR_PORT
        self._ircc_port: int = DEFAULT_IRCC_PORT
        self._mac: str | None = None
        self._pin: str | None = None
        self._device: SonyDevice | None = None

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> TVSideViewOptionsFlow:
        return TVSideViewOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            self._host = user_input[CONF_HOST].strip()
            self._name = user_input.get(CONF_NAME, DEFAULT_NAME)
            self._app_port = user_input.get(CONF_APP_PORT, DEFAULT_APP_PORT)
            self._dmr_port = user_input.get(CONF_DMR_PORT, DEFAULT_DMR_PORT)
            self._ircc_port = user_input.get(CONF_IRCC_PORT, DEFAULT_IRCC_PORT)

            try:
                self._mac = _normalize_mac(user_input.get(CONF_MAC))
            except vol.Invalid:
                errors[CONF_MAC] = "invalid_mac"
            else:
                await self.async_set_unique_id(f"tv_sideview_{self._host}")
                self._abort_if_unique_id_configured()

                try:
                    result = await self.hass.async_add_executor_job(
                        self._start_registration
                    )
                except CannotConnect:
                    errors["base"] = "cannot_connect"
                except Exception:  # noqa: BLE001
                    _LOGGER.exception("Unexpected error during registration")
                    errors["base"] = "unknown"
                else:
                    if result == AuthenticationResult.SUCCESS:
                        return await self._async_after_auth(pin=None)
                    if result == AuthenticationResult.PIN_NEEDED:
                        return await self.async_step_pin()
                    errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=_user_schema(
                {
                    CONF_HOST: self._host or "",
                    CONF_NAME: self._name,
                    CONF_MAC: self._mac or "",
                    CONF_APP_PORT: self._app_port,
                    CONF_DMR_PORT: self._dmr_port,
                    CONF_IRCC_PORT: self._ircc_port,
                }
            ),
            errors=errors,
        )

    async def async_step_pin(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            pin = user_input[CONF_PIN].strip()
            try:
                ok = await self.hass.async_add_executor_job(
                    self._finish_registration, pin
                )
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error during PIN auth")
                errors["base"] = "unknown"
            else:
                if ok:
                    return await self._async_after_auth(pin=pin)
                errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="pin",
            data_schema=PIN_SCHEMA,
            errors=errors,
            description_placeholders={"host": self._host or ""},
        )

    async def async_step_mac(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Optional MAC when device did not report one (needed for power-on / WOL)."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                self._mac = _normalize_mac(user_input.get(CONF_MAC))
            except vol.Invalid:
                errors[CONF_MAC] = "invalid_mac"
            else:
                return self._create_entry()

        discovered = None
        if self._device and self._device.mac:
            discovered = self._device.mac

        return self.async_show_form(
            step_id="mac",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_MAC,
                        default=discovered or self._mac or "",
                    ): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "host": self._host or "",
                "hint": discovered or "not detected — enter manually for Wake-on-LAN",
            },
        )

    async def _async_after_auth(self, pin: str | None) -> FlowResult:
        assert self._device is not None
        await self.hass.async_add_executor_job(self._device.init_device)
        self._pin = pin or self._device.pin

        # Prefer user-entered MAC, else auto from device
        if not self._mac and self._device.mac:
            self._mac = _normalize_mac(self._device.mac)

        if self._mac:
            self._device.mac = self._mac
            return self._create_entry()

        # Ask once if still unknown (power-on needs WOL on many BDVs)
        return await self.async_step_mac()

    def _create_entry(self) -> FlowResult:
        assert self._device is not None
        data = {
            CONF_HOST: self._host,
            CONF_NAME: self._name,
            CONF_APP_PORT: self._app_port,
            CONF_DMR_PORT: self._dmr_port,
            CONF_IRCC_PORT: self._ircc_port,
            CONF_PIN: self._pin,
            CONF_MAC: self._mac or self._device.mac,
        }
        return self.async_create_entry(title=self._name, data=data)

    def _start_registration(self) -> AuthenticationResult:
        assert self._host is not None
        self._device = SonyDevice(
            self._host,
            self._name,
            psk=None,
            app_port=self._app_port,
            dmr_port=self._dmr_port,
            ircc_port=self._ircc_port,
        )
        if self._mac:
            self._device.mac = self._mac
        try:
            return self._device.register()
        except Exception as err:
            _LOGGER.debug("register() failed: %s", err)
            raise CannotConnect from err

    def _finish_registration(self, pin: str) -> bool:
        assert self._device is not None
        self._device.pin = pin
        return bool(self._device.send_authentication(pin))


class TVSideViewOptionsFlow(config_entries.OptionsFlow):
    """Options: update MAC / ports without re-pairing."""

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                mac = _normalize_mac(user_input.get(CONF_MAC))
            except vol.Invalid:
                errors[CONF_MAC] = "invalid_mac"
            else:
                data = {**self._entry.data}
                data[CONF_MAC] = mac
                data[CONF_APP_PORT] = user_input.get(
                    CONF_APP_PORT, data.get(CONF_APP_PORT, DEFAULT_APP_PORT)
                )
                data[CONF_DMR_PORT] = user_input.get(
                    CONF_DMR_PORT, data.get(CONF_DMR_PORT, DEFAULT_DMR_PORT)
                )
                data[CONF_IRCC_PORT] = user_input.get(
                    CONF_IRCC_PORT, data.get(CONF_IRCC_PORT, DEFAULT_IRCC_PORT)
                )
                self.hass.config_entries.async_update_entry(self._entry, data=data)
                return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_MAC,
                        default=self._entry.data.get(CONF_MAC) or "",
                    ): str,
                    vol.Optional(
                        CONF_APP_PORT,
                        default=self._entry.data.get(
                            CONF_APP_PORT, DEFAULT_APP_PORT
                        ),
                    ): int,
                    vol.Optional(
                        CONF_DMR_PORT,
                        default=self._entry.data.get(
                            CONF_DMR_PORT, DEFAULT_DMR_PORT
                        ),
                    ): int,
                    vol.Optional(
                        CONF_IRCC_PORT,
                        default=self._entry.data.get(
                            CONF_IRCC_PORT, DEFAULT_IRCC_PORT
                        ),
                    ): int,
                }
            ),
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
