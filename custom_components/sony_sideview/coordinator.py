"""Data update coordinator for Sony SideView devices."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.const import STATE_OFF, STATE_ON, STATE_PAUSED, STATE_PLAYING
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from sonyapilib.device import SonyDevice

from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class SonyDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll power / playback state from a Sony SideView device."""

    def __init__(self, hass: HomeAssistant, device: SonyDevice) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.device = device

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch latest state from the device."""
        try:
            return await self.hass.async_add_executor_job(self._update)
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Sony device: {err}") from err

    def _update(self) -> dict[str, Any]:
        power = False
        try:
            power = bool(self.device.get_power_status())
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("get_power_status failed: %s", err)

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
        try:
            raw = self.device.get_volume()
            if raw is not None:
                volume = max(0.0, min(1.0, float(raw) / 100.0))
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("get_volume failed: %s", err)

        return {
            "state": state,
            "volume_level": volume,
            "mac": self.device.mac,
            "nickname": self.device.nickname,
        }
