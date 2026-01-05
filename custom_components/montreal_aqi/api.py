from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

from montreal_aqi_api import get_station_aqi, list_open_stations

_LOGGER = logging.getLogger(__name__)


class MontrealAQIApi:
    """Async wrapper for montreal-aqi-api."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def async_list_stations(self) -> list[dict[str, Any]]:
        _LOGGER.debug("API: Listing open stations")
        return await self.hass.async_add_executor_job(list_open_stations)

    async def async_get_station(self, station_id: str) -> dict[str, Any] | None:
        _LOGGER.debug("API: Fetching AQI for station %s", station_id)
        station = await self.hass.async_add_executor_job(get_station_aqi, station_id)
        if station is None:
            return None
        return cast("dict[str, Any]", station.to_dict())
