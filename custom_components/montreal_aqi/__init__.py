from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import MontrealAQIClient
from .const import DOMAIN, CONF_STATION_ID, UPDATE_INTERVAL_MINUTES

LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    station_id: str = entry.data[CONF_STATION_ID]

    client = MontrealAQIClient(station_id)

    async def async_update_data():
        station = await hass.async_add_executor_job(client.fetch_station)
        if station is None:
            raise UpdateFailed("No AQI data returned")
        return station

    coordinator = DataUpdateCoordinator(
        hass,
        LOGGER,
        name=f"Montreal AQI ({station_id})",
        update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
        update_method=async_update_data,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


# import logging

# from homeassistant.config_entries import ConfigEntry
# from homeassistant.core import HomeAssistant

# from .const import DOMAIN

# _LOGGER = logging.getLogger(__name__)


# async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
#     """Set up the Montreal AQI integration from a config entry."""
#     _LOGGER.debug("Setting up Montreal AQI integration")
#     hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry.data

#     await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

#     return True


# async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
#     """Unload a config entry."""
#     if entry.entry_id in hass.data[DOMAIN]:
#         hass.data[DOMAIN].pop(entry.entry_id)

#     # Unload the platform
#     return await hass.config_entries.async_forward_entry_unload(entry, "sensor")
