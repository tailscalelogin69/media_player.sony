"""Video & TV SideView (Legacy API) integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
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
from .coordinator import SideViewDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER, Platform.REMOTE]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Video & TV SideView from a config entry.

    The device is often powered off at HA restart. Setup must still succeed so
    entities exist (state defaults to off) and update when the unit is reachable.
    """
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

    # Soft init: offline is normal — do not raise ConfigEntryNotReady
    try:
        await hass.async_add_executor_job(_try_init_device, device, pin)
    except ConfigEntryAuthFailed:
        raise
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning(
            "SideView device at %s is offline or not ready at setup (%s); "
            "entities will show off until it is reachable",
            host,
            err,
        )

    if mac:
        device.mac = mac
    elif device.mac and not entry.data.get(CONF_MAC):
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_MAC: device.mac}
        )

    coordinator = SideViewDataUpdateCoordinator(hass, device)
    # Soft first refresh — offline must not block entity registration
    await coordinator.async_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    logging.getLogger("sonyapilib").setLevel(logging.WARNING)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


def _try_init_device(device: SonyDevice, pin: str | None) -> None:
    """Init when online. Re-register only if no stored PIN (first-time style)."""
    if not pin or pin in ("0000", ""):
        result = device.register()
        if result == AuthenticationResult.PIN_NEEDED:
            raise ConfigEntryAuthFailed("PIN required — reconfigure the integration")
        if result != AuthenticationResult.SUCCESS:
            raise ConfigEntryAuthFailed("Registration failed")
        return

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
