from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .const import CONF_STATION_ID, DOMAIN, PLATFORMS

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Montreal AQI from a config entry."""
    _LOGGER.debug("Setting up entry %s", entry.entry_id)

    from .api import MontrealAQIApi
    from .coordinator import MontrealAQICoordinator

    api = MontrealAQIApi(hass)

    coordinator = MontrealAQICoordinator(
        hass=hass,
        api=api,
        station_id=entry.data[CONF_STATION_ID],
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading entry %s", entry.entry_id)

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
