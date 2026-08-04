"""The Sony Legacy (SideView) integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
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
from .coordinator import SonyDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER, Platform.REMOTE]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Sony Legacy from a config entry."""
    host = entry.data[CONF_HOST]
    name = entry.data.get(CONF_NAME, DEFAULT_NAME)
    pin = entry.data.get(CONF_PIN)
    app_port = entry.data.get(CONF_APP_PORT, DEFAULT_APP_PORT)
    dmr_port = entry.data.get(CONF_DMR_PORT, DEFAULT_DMR_PORT)
    ircc_port = entry.data.get(CONF_IRCC_PORT, DEFAULT_IRCC_PORT)
    mac = entry.data.get(CONF_MAC)

    device = SonyDevice(
        host,
        name,
        psk=None,
        app_port=app_port,
        dmr_port=dmr_port,
        ircc_port=ircc_port,
    )
    if pin:
        device.pin = pin
    if mac:
        device.mac = mac

    try:
        # Ensure the device is initialised / authenticated.
        await hass.async_add_executor_job(_ensure_authenticated, device, pin)
    except ConfigEntryAuthFailed:
        raise
    except Exception as err:
        raise ConfigEntryNotReady(f"Unable to connect to Sony device at {host}: {err}") from err

    coordinator = SonyDataUpdateCoordinator(hass, device)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Quiet the noisy underlying library unless debugging.
    logging.getLogger("sonyapilib").setLevel(logging.WARNING)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


def _ensure_authenticated(device: SonyDevice, pin: str | None) -> None:
    """Run blocking auth / init on the executor."""
    if not pin or pin in ("0000", ""):
        result = device.register()
        if result == AuthenticationResult.PIN_NEEDED:
            raise ConfigEntryAuthFailed("PIN required — reconfigure the integration")
        if result != AuthenticationResult.SUCCESS:
            raise ConfigEntryAuthFailed("Registration failed")
    else:
        # PIN already stored — initialise device (loads commands, mac, etc.)
        device.init_device()


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
