from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

import aiohttp
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

    async def async_get_aqi_fallback(
        self, station_id: str, hour: str | None = None
    ) -> dict[str, Any] | None:
        """Fetch AQI data from fallback source (Ckan datastore) if primary source insufficient.

        This is used when detailed pollutant data is unavailable but we still want
        to provide an AQI value from the Montreal open data.

        Args:
            station_id: Station ID (as string)
            hour: Hour to search for (0-23), or None to get the most recent

        Returns:
            Dictionary with 'aqi' and 'dominant_pollutant' keys
            or None if fallback data unavailable

        Raises:
            Exception: If API call fails
        """
        _LOGGER.debug(
            "API: Fetching AQI fallback for station %s from Ckan (hour: %s)",
            station_id,
            hour or "latest",
        )

        try:
            # Ckan datastore API endpoint
            ckan_url = "https://donnees.montreal.ca/api/3/action/datastore_search"
            resource_id = "6554355e-63d1-4a01-a268-91e0763c3606"

            filters: dict[str, Any] = {"stationId": station_id}
            if hour is not None:
                filters["heure"] = hour

            params: dict[str, Any] = {
                "resource_id": resource_id,
                "filters": filters,
                "sort": "date desc, heure desc",
                "limit": 50,
            }

            async with (
                aiohttp.ClientSession() as session,
                session.get(
                    ckan_url,
                    params=params,  # type: ignore[arg-type]
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp,
            ):
                if resp.status != 200:
                    _LOGGER.warning(
                        "API: Ckan fallback returned status %d for station %s",
                        resp.status,
                        station_id,
                    )
                    return None
                data = await resp.json()

            if not data.get("success"):
                _LOGGER.warning(
                    "API: Ckan fallback request failed for station %s",
                    station_id,
                )
                return None

            records = data.get("result", {}).get("records", [])
            if not records:
                _LOGGER.warning(
                    "API: No fallback data found for station %s in Ckan",
                    station_id,
                )
                return None

            # Get the most recent record (already sorted by date desc, heure desc)
            record = records[0]
            aqi_value = int(float(record.get("valeur", 0)))
            dominant_pollutant = record.get("pollutant")

            _LOGGER.debug(
                "API: Retrieved fallback AQI for station %s (AQI: %s, pollutant: %s)",
                station_id,
                aqi_value,
                dominant_pollutant,
            )

            return {
                "aqi": aqi_value,
                "dominant_pollutant": dominant_pollutant,
            }

        except Exception as err:
            _LOGGER.warning(
                "API: error fetching fallback AQI for station %s: %s",
                station_id,
                err,
            )
            return None
