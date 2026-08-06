"""Data update coordinator for SideView devices."""

from __future__ import annotations

import logging
import socket
from typing import Any

import requests
from homeassistant.const import STATE_OFF, STATE_ON, STATE_PAUSED, STATE_PLAYING
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from sonyapilib.device import SonyDevice

from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

# Default when the device cannot be reached (normal if powered off)
_OFFLINE_DATA: dict[str, Any] = {
    "state": STATE_OFF,
    "volume_level": None,
    "available": False,
    "mac": None,
    "nickname": None,
}


class SideViewDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll power / playback / volume from a SideView device.

    Never fails the integration when the device is off — returns off state.
    """

    def __init__(self, hass: HomeAssistant, device: SonyDevice) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.device = device
        self._device_ready = bool(device.commands or device.actions)

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.hass.async_add_executor_job(self._update)
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Update failed (treating as offline): %s", err)
            return {
                **_OFFLINE_DATA,
                "mac": self.device.mac,
                "nickname": self.device.nickname,
            }

    def _probe_reachable(self) -> bool:
        """Return True if the device answers on DMR (network awake)."""
        try:
            if self.device.get_power_status():
                return True
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("get_power_status failed: %s", err)

        try:
            resp = requests.get(self.device.dmr_url, timeout=3)
            if resp.status_code == 200:
                return True
        except requests.RequestException as err:
            _LOGGER.debug("DMR probe failed: %s", err)

        try:
            with socket.create_connection(
                (self.device.host, self.device.dmr_port), timeout=2
            ):
                return True
        except OSError as err:
            _LOGGER.debug("TCP probe failed: %s", err)

        return False

    def _ensure_device_ready(self) -> None:
        """Re-run init_device once the unit is reachable after being offline."""
        if self._device_ready:
            return
        try:
            self.device.init_device()
            self._device_ready = bool(self.device.commands or self.device.actions)
            if self._device_ready:
                _LOGGER.info(
                    "SideView device at %s is reachable; command list loaded",
                    self.device.host,
                )
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("init_device while online failed: %s", err)
            self._device_ready = False

    def _update(self) -> dict[str, Any]:
        power = self._probe_reachable()

        if not power:
            return {
                "state": STATE_OFF,
                "volume_level": None,
                "available": False,
                "mac": self.device.mac,
                "nickname": self.device.nickname,
            }

        # Device answered — load IRCC/command metadata if setup was offline
        self._ensure_device_ready()

        state = STATE_ON
        try:
            status = (self.device.get_playing_status() or "").lower()
            if "playing" in status:
                state = STATE_PLAYING
            elif "pause" in status:
                state = STATE_PAUSED
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("get_playing_status failed: %s", err)

        volume: float | None = None
        try:
            raw = self.device.get_volume()
            if raw is not None and int(raw) >= 0:
                volume = max(0.0, min(1.0, float(raw) / 100.0))
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("get_volume failed: %s", err)

        return {
            "state": state,
            "volume_level": volume,
            "available": True,
            "mac": self.device.mac,
            "nickname": self.device.nickname,
        }
