"""Remote platform for Sony Legacy devices."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable
from typing import Any

from homeassistant.components.remote import (
    ATTR_DELAY_SECS,
    ATTR_NUM_REPEATS,
    DEFAULT_DELAY_SECS,
    DEFAULT_NUM_REPEATS,
    RemoteEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import COMMANDS, DOMAIN
from .coordinator import SonyDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the remote from a config entry."""
    coordinator: SonyDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SonyRemote(coordinator, entry)])


class SonyRemote(CoordinatorEntity[SonyDataUpdateCoordinator], RemoteEntity):
    """Remote entity that sends IRCC commands to a Sony SideView device."""

    _attr_has_entity_name = True
    _attr_name = "Remote"

    def __init__(self, coordinator: SonyDataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        host = entry.data[CONF_HOST]
        self._attr_unique_id = f"{host}_remote"
        mac = coordinator.device.mac or coordinator.data.get("mac")
        identifiers = {(DOMAIN, mac)} if mac else {(DOMAIN, host)}
        self._attr_device_info = DeviceInfo(
            identifiers=identifiers,
            name=entry.data.get(CONF_NAME, coordinator.device.nickname),
            manufacturer="Sony",
            model="SideView / Legacy API",
            connections={("mac", mac)} if mac else set(),
        )

    @property
    def is_on(self) -> bool | None:
        state = self.coordinator.data.get("state")
        if state is None:
            return None
        return str(state) != "off"

    @property
    def activity_list(self) -> list[str] | None:
        """Expose known command names as activities for UI convenience."""
        # Prefer live command list from the device when available.
        cmds = list(self.coordinator.device.commands.keys()) if self.coordinator.device.commands else COMMANDS
        return sorted(cmds)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.hass.async_add_executor_job(self.coordinator.device.power, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.hass.async_add_executor_job(self.coordinator.device.power, False)
        await self.coordinator.async_request_refresh()

    async def async_send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        """Send one or more IRCC commands."""
        repeats = kwargs.get(ATTR_NUM_REPEATS, DEFAULT_NUM_REPEATS)
        delay = kwargs.get(ATTR_DELAY_SECS, DEFAULT_DELAY_SECS)

        for _ in range(repeats):
            for cmd in command:
                _LOGGER.debug("Sending IRCC command: %s", cmd)
                await self.hass.async_add_executor_job(
                    self.coordinator.device._send_command, cmd  # noqa: SLF001
                )
                if delay:
                    await asyncio.sleep(delay)

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
