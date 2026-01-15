from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .api import MontrealAQIApi

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .const import DOMAIN, PPB_TO_UGM3, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class MontrealAQICoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for Montreal AQI data fetching."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: MontrealAQIApi,
        station_id: str,
    ) -> None:
        """Initialize coordinator.

        Args:
            hass: Home Assistant instance
            api: Montreal AQI API wrapper
            station_id: Station ID as string
        """
        self.api = api
        self.station_id = station_id

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{station_id}",
            update_interval=UPDATE_INTERVAL,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch and process data from API."""
        _LOGGER.debug(
            "Coordinator: updating data for station %s",
            self.station_id,
        )

        try:
            data = await self.api.async_get_station(self.station_id)
        except Exception as err:
            _LOGGER.error(
                "Error fetching Montreal AQI data for station %s: %s",
                self.station_id,
                err,
                exc_info=True,
            )
            raise UpdateFailed(
                f"Cannot fetch data for station {self.station_id}"
            ) from err

        if not data:
            _LOGGER.warning(
                "Coordinator: no data available for station %s (station may not have current measurements)",
                self.station_id,
            )
            raise UpdateFailed(
                f"No data available for station {self.station_id}. "
                "Station may not have current measurements or may be offline."
            )

        # Validate required fields
        if "aqi" not in data:
            _LOGGER.warning(
                "Coordinator: missing 'aqi' field in response for station %s",
                self.station_id,
            )
            raise UpdateFailed("Missing AQI value in API response")

        # Process timestamp
        timestamp_str = data.get("timestamp")
        timestamp = None
        if timestamp_str:
            try:
                parsed = dt_util.parse_datetime(timestamp_str)
                if parsed is not None:
                    # Add 50 minutes as per Montreal data documentation
                    timestamp = parsed + timedelta(minutes=50)
                else:
                    _LOGGER.warning(
                        "Coordinator: failed to parse timestamp '%s' for station %s",
                        timestamp_str,
                        self.station_id,
                    )
            except Exception as err:
                _LOGGER.warning(
                    "Coordinator: error parsing timestamp for station %s: %s",
                    self.station_id,
                    err,
                )

        # Process pollutants with unit conversion
        pollutants = data.get("pollutants", {})
        processed_pollutants = self._convert_pollutants(pollutants)

        return {
            "aqi": data.get("aqi"),
            "dominant_pollutant": data.get("dominant_pollutant"),
            "pollutants": processed_pollutants,
            "timestamp": timestamp,
        }

    def _convert_pollutants(
        self, pollutants: dict[str, Any]
    ) -> dict[str, dict[str, float | None]]:
        """Convert pollutant units from PPB to µg/m³ if needed, keeping concentration key."""
        converted: dict[str, dict[str, float | None]] = {}
        for pollutant_name, value in pollutants.items():
            raw_value = (
                value.get("concentration")
                if isinstance(value, dict) and "concentration" in value
                else value
            )

            if raw_value is None:
                converted[pollutant_name] = {"concentration": None}
                continue

            try:
                float_value = float(raw_value)
            except (ValueError, TypeError):
                _LOGGER.warning(
                    "Coordinator: invalid pollutant value for %s: %s",
                    pollutant_name,
                    value,
                )
                converted[pollutant_name] = {"concentration": None}
                continue

            if pollutant_name in PPB_TO_UGM3:
                converted_value: float | int = round(
                    float_value * PPB_TO_UGM3[pollutant_name]
                )
            else:
                converted_value = int(float_value)

            converted[pollutant_name] = {"concentration": converted_value}

        return converted
