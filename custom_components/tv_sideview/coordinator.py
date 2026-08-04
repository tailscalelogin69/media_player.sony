"""Data update coordinator for SideView devices."""

from __future__ import annotations

import logging
import socket
from typing import Any

import requests
from homeassistant.const import STATE_OFF, STATE_ON, STATE_PAUSED, STATE_PLAYING
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from sonyapilib.device import SonyDevice

from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class SideViewDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll power / playback / volume from a SideView device."""

    def __init__(self, hass: HomeAssistant, device: SonyDevice) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.device = device

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.hass.async_add_executor_job(self._update)
        except Exception as err:
            raise UpdateFailed(f"Error communicating with SideView device: {err}") from err

    def _probe_reachable(self) -> bool:
        """Return True if the device answers on DMR (network awake)."""
        # 1) Library power check (actionList / JSON API depending on generation)
        try:
            if self.device.get_power_status():
                return True
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("get_power_status failed: %s", err)

        # 2) Direct DMR HTTP probe — works on BDV-E4100 when actionList is flaky
        try:
            resp = requests.get(self.device.dmr_url, timeout=3)
            if resp.status_code == 200:
                return True
        except requests.RequestException as err:
            _LOGGER.debug("DMR probe failed: %s", err)

        # 3) TCP connect to DMR port as last resort
        try:
            with socket.create_connection(
                (self.device.host, self.device.dmr_port), timeout=2
            ):
                return True
        except OSError as err:
            _LOGGER.debug("TCP probe failed: %s", err)

        return False

    def _update(self) -> dict[str, Any]:
        power = self._probe_reachable()

        state = STATE_OFF
        if power:
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
        if power:
            try:
                raw = self.device.get_volume()
                # sonyapilib returns -1 on failure
                if raw is not None and int(raw) >= 0:
                    volume = max(0.0, min(1.0, float(raw) / 100.0))
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("get_volume failed: %s", err)

        return {
            "state": state,
            "volume_level": volume,
            "available": power,
            "mac": self.device.mac,
            "nickname": self.device.nickname,
        }
