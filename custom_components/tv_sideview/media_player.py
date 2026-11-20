"""Media player platform for SideView devices."""

from __future__ import annotations

import asyncio
import logging
import socket
import time

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_MAC, DOMAIN
from .coordinator import SideViewDataUpdateCoordinator
from .ircc import send_command, wol_wait_seconds

_LOGGER = logging.getLogger(__name__)

SUPPORT_SIDEVIEW = (
    MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.PLAY
    | MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.STOP
    | MediaPlayerEntityFeature.NEXT_TRACK
    | MediaPlayerEntityFeature.PREVIOUS_TRACK
    | MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.VOLUME_SET
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SideViewDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SideViewMediaPlayer(coordinator, entry)])


class SideViewMediaPlayer(
    CoordinatorEntity[SideViewDataUpdateCoordinator], MediaPlayerEntity
):
    """Representation of a SideView media player."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_device_class = MediaPlayerDeviceClass.RECEIVER
    _attr_supported_features = SUPPORT_SIDEVIEW

    def __init__(
        self, coordinator: SideViewDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        host = entry.data[CONF_HOST]
        self._attr_unique_id = f"tv_sideview_{host}_media_player"
        mac = (
            entry.data.get(CONF_MAC)
            or coordinator.device.mac
            or (coordinator.data or {}).get("mac")
        )
        identifiers = {(DOMAIN, mac)} if mac else {(DOMAIN, host)}
        self._attr_device_info = DeviceInfo(
            identifiers=identifiers,
            name=entry.data.get(CONF_NAME, coordinator.device.nickname),
            manufacturer="Sony",
            model="BDV / SideView",
            connections={("mac", mac)} if mac else set(),
        )
        if mac and not coordinator.device.mac:
            coordinator.device.mac = mac

    @property
    def available(self) -> bool:
        # Always provided by the integration — off when device is unreachable
        return True

    @property
    def state(self) -> MediaPlayerState:
        if not self.coordinator.data:
            return MediaPlayerState.OFF
        raw = self.coordinator.data.get("state")
        if raw is None:
            return MediaPlayerState.OFF
        mapping = {
            "on": MediaPlayerState.ON,
            "off": MediaPlayerState.OFF,
            "playing": MediaPlayerState.PLAYING,
            "paused": MediaPlayerState.PAUSED,
        }
        return mapping.get(str(raw), MediaPlayerState.OFF)

    @property
    def volume_level(self) -> float | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("volume_level")

    def _port_open(self, port: int | None) -> bool:
        if not port:
            return False
        try:
            with socket.create_connection((self.coordinator.device.host, port), timeout=2):
                return True
        except OSError:
            return False

    def _send(self, name: str) -> bool:
        device = self.coordinator.device
        if send_command(device, name, self.coordinator.resolved_profile()):
            return True
        try:
            device._send_command(name)  # noqa: SLF001
            return True
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Fallback command %s failed: %s", name, err)
            return False

    def _power_on_blocking(self) -> None:
        """Wake the NIC, wait for the stack, then send Power.

        The SideView app waits up to 120s (40s only for a Blu-ray recorder)
        for the unit to reappear after the magic packet. Firing Power before the
        IRCC port is open is why turn-on used to no-op. The wait ends as soon
        as IRCC or DMR answers.
        """
        device = self.coordinator.device
        mac = self._entry.data.get(CONF_MAC) or device.mac
        if mac:
            device.mac = mac
            try:
                import wakeonlan

                for _ in range(3):
                    wakeonlan.send_magic_packet(mac.replace(":", "-"))
                    time.sleep(0.2)
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("WOL failed: %s", err)

        deadline = time.time() + wol_wait_seconds(self.coordinator.resolved_profile())
        while time.time() < deadline:
            if self._port_open(device.ircc_port) or self._port_open(device.dmr_port):
                break
            time.sleep(2)

        if not self._send("Power"):
            try:
                device.power(True)
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("device.power(True) failed: %s", err)

    async def async_turn_on(self) -> None:
        await self.hass.async_add_executor_job(self._power_on_blocking)
        for _ in range(8):
            await asyncio.sleep(2)
            await self.coordinator.async_request_refresh()
            if self.coordinator.data and self.coordinator.data.get("state") != "off":
                break

    async def async_turn_off(self) -> None:
        await self.hass.async_add_executor_job(self._send, "Power")
        await asyncio.sleep(2)
        await self.coordinator.async_request_refresh()

    async def async_media_play(self) -> None:
        await self.hass.async_add_executor_job(self._send, "Play")
        await self.coordinator.async_request_refresh()

    async def async_media_pause(self) -> None:
        await self.hass.async_add_executor_job(self._send, "Pause")
        await self.coordinator.async_request_refresh()

    async def async_media_stop(self) -> None:
        await self.hass.async_add_executor_job(self._send, "Stop")
        await self.coordinator.async_request_refresh()

    async def async_media_next_track(self) -> None:
        await self.hass.async_add_executor_job(self._send, "Next")

    async def async_media_previous_track(self) -> None:
        await self.hass.async_add_executor_job(self._send, "Prev")

    async def async_volume_up(self) -> None:
        await self.hass.async_add_executor_job(self._send, "VolumeUp")
        await self.coordinator.async_request_refresh()

    async def async_volume_down(self) -> None:
        await self.hass.async_add_executor_job(self._send, "VolumeDown")
        await self.coordinator.async_request_refresh()

    async def async_set_volume_level(self, volume: float) -> None:
        await self.hass.async_add_executor_job(
            self.coordinator.device.set_volume, int(round(volume * 100))
        )
        await self.coordinator.async_request_refresh()

    async def async_mute_volume(self, mute: bool) -> None:
        await self.hass.async_add_executor_job(self._send, "Mute")
        await self.coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
