"""Config flow for Sony SideView (Legacy API)."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME
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

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Optional(CONF_APP_PORT, default=DEFAULT_APP_PORT): int,
        vol.Optional(CONF_DMR_PORT, default=DEFAULT_DMR_PORT): int,
        vol.Optional(CONF_IRCC_PORT, default=DEFAULT_IRCC_PORT): int,
    }
)

PIN_SCHEMA = vol.Schema({vol.Required(CONF_PIN): str})


class SonySideViewConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Sony SideView (Legacy API)."""

    VERSION = 1

    def __init__(self) -> None:
        self._host: str | None = None
        self._name: str = DEFAULT_NAME
        self._app_port: int = DEFAULT_APP_PORT
        self._dmr_port: int = DEFAULT_DMR_PORT
        self._ircc_port: int = DEFAULT_IRCC_PORT
        self._device: SonyDevice | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._host = user_input[CONF_HOST].strip()
            self._name = user_input.get(CONF_NAME, DEFAULT_NAME)
            self._app_port = user_input.get(CONF_APP_PORT, DEFAULT_APP_PORT)
            self._dmr_port = user_input.get(CONF_DMR_PORT, DEFAULT_DMR_PORT)
            self._ircc_port = user_input.get(CONF_IRCC_PORT, DEFAULT_IRCC_PORT)

            await self.async_set_unique_id(f"sony_sideview_{self._host}")
            self._abort_if_unique_id_configured()

            try:
                result = await self.hass.async_add_executor_job(self._start_registration)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error during registration")
                errors["base"] = "unknown"
            else:
                if result == AuthenticationResult.SUCCESS:
                    return await self._async_create_entry(pin=None)
                if result == AuthenticationResult.PIN_NEEDED:
                    return await self.async_step_pin()
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=USER_SCHEMA,
            errors=errors,
        )

    async def async_step_pin(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Ask the user for the PIN shown on the device."""
        errors: dict[str, str] = {}

        if user_input is not None:
            pin = user_input[CONF_PIN].strip()
            try:
                ok = await self.hass.async_add_executor_job(self._finish_registration, pin)
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error during PIN auth")
                errors["base"] = "unknown"
            else:
                if ok:
                    return await self._async_create_entry(pin=pin)
                errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="pin",
            data_schema=PIN_SCHEMA,
            errors=errors,
            description_placeholders={"host": self._host or ""},
        )

    def _start_registration(self) -> AuthenticationResult:
        """Create device and call register() (blocking)."""
        assert self._host is not None
        self._device = SonyDevice(
            self._host,
            self._name,
            psk=None,
            app_port=self._app_port,
            dmr_port=self._dmr_port,
            ircc_port=self._ircc_port,
        )
        try:
            return self._device.register()
        except Exception as err:
            _LOGGER.debug("register() failed: %s", err)
            raise CannotConnect from err

    def _finish_registration(self, pin: str) -> bool:
        """Send PIN and initialise device (blocking)."""
        assert self._device is not None
        self._device.pin = pin
        return bool(self._device.send_authentication(pin))

    async def _async_create_entry(self, pin: str | None) -> FlowResult:
        """Create the config entry with stored credentials."""
        assert self._device is not None
        await self.hass.async_add_executor_job(self._device.init_device)

        data = {
            CONF_HOST: self._host,
            CONF_NAME: self._name,
            CONF_APP_PORT: self._app_port,
            CONF_DMR_PORT: self._dmr_port,
            CONF_IRCC_PORT: self._ircc_port,
            CONF_PIN: pin or self._device.pin,
            CONF_MAC: self._device.mac,
        }
        return self.async_create_entry(title=self._name, data=data)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
