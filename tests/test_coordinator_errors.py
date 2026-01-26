"""Tests for Coordinator error handling."""

from unittest.mock import AsyncMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.montreal_aqi.coordinator import MontrealAQICoordinator


async def test_coordinator_api_error(hass: HomeAssistant) -> None:
    """Test coordinator handles API errors."""
    api = AsyncMock()
    api.async_get_station.side_effect = RuntimeError("API failed")

    coordinator = MontrealAQICoordinator(
        hass=hass,
        api=api,
        station_id="80",
    )

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


async def test_coordinator_no_data(hass: HomeAssistant) -> None:
    """Test coordinator handles when API returns None."""
    api = AsyncMock()
    api.async_get_station.return_value = None

    coordinator = MontrealAQICoordinator(
        hass=hass,
        api=api,
        station_id="80",
    )

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


async def test_coordinator_missing_aqi_field(hass: HomeAssistant) -> None:
    """Test coordinator handles missing AQI field."""
    api = AsyncMock()
    api.async_get_station.return_value = {
        "dominant_pollutant": "PM2.5",
        "pollutants": {},
        "timestamp": "2025-01-15T13:00:00",
    }

    coordinator = MontrealAQICoordinator(
        hass=hass,
        api=api,
        station_id="80",
    )

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


async def test_coordinator_invalid_timestamp(hass: HomeAssistant) -> None:
    """Test coordinator handles invalid timestamp gracefully."""
    api = AsyncMock()
    api.async_get_station.return_value = {
        "aqi": 42,
        "dominant_pollutant": "PM2.5",
        "pollutants": {},
        "timestamp": "invalid-date",
    }

    coordinator = MontrealAQICoordinator(
        hass=hass,
        api=api,
        station_id="80",
    )

    data = await coordinator._async_update_data()
    assert data["aqi"] == 42
    assert data["timestamp"] is None


async def test_coordinator_invalid_pollutant_value(hass: HomeAssistant) -> None:
    """Test coordinator handles invalid pollutant values."""
    api = AsyncMock()
    api.async_get_station.return_value = {
        "aqi": 42,
        "dominant_pollutant": "PM2.5",
        "pollutants": {
            "PM2.5": {"concentration": "invalid"},
            "NO2": {"concentration": 30},  # Will be converted: 30 * (46.01/24.45) ≈ 56
        },
        "timestamp": "2025-01-15T13:00:00",
    }

    coordinator = MontrealAQICoordinator(
        hass=hass,
        api=api,
        station_id="80",
    )

    data = await coordinator._async_update_data()
    assert data["pollutants"]["PM2.5"]["concentration"] is None
    # NO2 is converted from PPB to µg/m³: 30 * (46.01/24.45) ≈ 56
    assert data["pollutants"]["NO2"]["concentration"] == 56


async def test_coordinator_null_pollutant_value(hass: HomeAssistant) -> None:
    """Test coordinator handles null pollutant values."""
    api = AsyncMock()
    api.async_get_station.return_value = {
        "aqi": 42,
        "dominant_pollutant": "PM2.5",
        "pollutants": {
            "PM2.5": {"concentration": None},
            "NO2": {"concentration": 30},  # Will be converted: 30 * (46.01/24.45) ≈ 56
        },
        "timestamp": "2025-01-15T13:00:00",
    }

    coordinator = MontrealAQICoordinator(
        hass=hass,
        api=api,
        station_id="80",
    )

    data = await coordinator._async_update_data()
    assert data["pollutants"]["PM2.5"]["concentration"] is None
    # NO2 is converted from PPB to µg/m³: 30 * (46.01/24.45) ≈ 56
    assert data["pollutants"]["NO2"]["concentration"] == 56
