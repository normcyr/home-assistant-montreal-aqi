from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

from montreal_aqi_api import get_station_aqi, list_open_stations

_LOGGER = logging.getLogger(__name__)


class MontrealAQIApi:
    """Async wrapper for montreal-aqi-api library."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize API wrapper.

        Args:
            hass: Home Assistant instance
        """
        self.hass = hass

    async def async_list_stations(self) -> list[dict[str, Any]]:
        """Fetch list of available monitoring stations.

        Returns:
            List of station dictionaries with 'station_id' and 'name' keys

        Raises:
            Exception: If API call fails
        """
        _LOGGER.debug("API: Listing open stations")
        try:
            stations = await self.hass.async_add_executor_job(list_open_stations)
            if not isinstance(stations, list):
                _LOGGER.error(
                    "API: unexpected return type from list_open_stations: %s",
                    type(stations),
                )
                return []
            _LOGGER.debug("API: Retrieved %d stations", len(stations))
            return stations
        except Exception as err:
            _LOGGER.error("API: error listing stations: %s", err, exc_info=True)
            raise

    async def async_get_station(self, station_id: str) -> dict[str, Any] | None:
        """Fetch AQI data for a specific station.

        Args:
            station_id: Station ID (as string)

        Returns:
            Dictionary with 'aqi', 'pollutants', 'dominant_pollutant', 'timestamp'
            or None if station not found

        Raises:
            Exception: If API call fails
        """
        _LOGGER.debug("API: Fetching AQI for station %s", station_id)
        try:
            station = await self.hass.async_add_executor_job(
                get_station_aqi, station_id
            )
            if station is None:
                _LOGGER.warning("API: station %s not found", station_id)
                return None

            station_dict = cast("dict[str, Any]", station.to_dict())
            _LOGGER.debug(
                "API: Retrieved data for station %s (AQI: %s)",
                station_id,
                station_dict.get("aqi"),
            )
            return station_dict
        except Exception as err:
            _LOGGER.error(
                "API: error fetching station %s: %s",
                station_id,
                err,
                exc_info=True,
            )
            raise
