"""Media player platform for SideView devices."""

from __future__ import annotations

import logging

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

from .const import DOMAIN
from .coordinator import SideViewDataUpdateCoordinator

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
        host = entry.data[CONF_HOST]
        self._attr_unique_id = f"tv_sideview_{host}_media_player"
        mac = coordinator.device.mac or coordinator.data.get("mac")
        identifiers = {(DOMAIN, mac)} if mac else {(DOMAIN, host)}
        self._attr_device_info = DeviceInfo(
            identifiers=identifiers,
            name=entry.data.get(CONF_NAME, coordinator.device.nickname),
            manufacturer="Sony",
            model="Video & TV SideView",
            connections={("mac", mac)} if mac else set(),
        )

    @property
    def state(self) -> MediaPlayerState | None:
        raw = self.coordinator.data.get("state")
        if raw is None:
            return None
        mapping = {
            "on": MediaPlayerState.ON,
            "off": MediaPlayerState.OFF,
            "playing": MediaPlayerState.PLAYING,
            "paused": MediaPlayerState.PAUSED,
        }
        return mapping.get(str(raw), MediaPlayerState.ON if raw else MediaPlayerState.OFF)

    @property
    def volume_level(self) -> float | None:
        return self.coordinator.data.get("volume_level")

    async def async_turn_on(self) -> None:
        await self.hass.async_add_executor_job(self.coordinator.device.power, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        await self.hass.async_add_executor_job(self.coordinator.device.power, False)
        await self.coordinator.async_request_refresh()

    async def async_media_play(self) -> None:
        await self.hass.async_add_executor_job(self.coordinator.device.play)
        await self.coordinator.async_request_refresh()

    async def async_media_pause(self) -> None:
        await self.hass.async_add_executor_job(self.coordinator.device.pause)
        await self.coordinator.async_request_refresh()

    async def async_media_stop(self) -> None:
        await self.hass.async_add_executor_job(self.coordinator.device.stop)
        await self.coordinator.async_request_refresh()

    async def async_media_next_track(self) -> None:
        await self.hass.async_add_executor_job(self.coordinator.device.next)

    async def async_media_previous_track(self) -> None:
        await self.hass.async_add_executor_job(self.coordinator.device.prev)

    async def async_volume_up(self) -> None:
        await self.hass.async_add_executor_job(self.coordinator.device.volume_up)
        await self.coordinator.async_request_refresh()

    async def async_volume_down(self) -> None:
        await self.hass.async_add_executor_job(self.coordinator.device.volume_down)
        await self.coordinator.async_request_refresh()

    async def async_set_volume_level(self, volume: float) -> None:
        await self.hass.async_add_executor_job(
            self.coordinator.device.set_volume, int(volume * 100)
        )
        await self.coordinator.async_request_refresh()

    async def async_mute_volume(self, mute: bool) -> None:
        await self.hass.async_add_executor_job(self.coordinator.device.mute)

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
