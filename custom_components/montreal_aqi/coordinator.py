from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import MontrealAQIApi
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class MontrealAQICoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for Montreal AQI."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: MontrealAQIApi,
        station_id: int,
    ) -> None:
        self.api = api
        self.station_id = station_id

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{station_id}",
            update_interval=UPDATE_INTERVAL,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        _LOGGER.debug(
            "Coordinator: updating data for station %s",
            self.station_id,
        )

        try:
            data = await self.api.async_get_station(str(self.station_id))

        except Exception as err:
            _LOGGER.exception(
                "Error fetching Montreal AQI data for station %s",
                self.station_id,
            )
            raise UpdateFailed(err) from err

        if not data:
            raise UpdateFailed("Empty response from Montreal AQI API")

        # data
        return {
            "aqi": data.get("aqi"),
            "dominant_pollutant": data.get("dominant_pollutant"),
            "pollutants": data.get("pollutants", {}),
            "timestamp": data.get("timestamp"),
        }
