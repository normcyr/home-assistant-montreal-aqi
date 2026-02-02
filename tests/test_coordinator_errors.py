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
        "pollutants": {
            "PM2.5": {"concentration": 12},
            "NO2": {"concentration": 30},
            "O3": {"concentration": 25},
        },
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
            "O3": {"concentration": 25},   # At least 3 pollutants required
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
            "SO2": {"concentration": 5},   # At least 3 pollutants required
            "O3": {"concentration": 25},
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


async def test_coordinator_insufficient_pollutants_one(hass: HomeAssistant) -> None:
    """Test coordinator rejects data with only 1 pollutant (sensor malfunction)."""
    api = AsyncMock()
    api.async_get_station.return_value = {
        "aqi": 42,
        "dominant_pollutant": "PM2.5",
        "pollutants": {
            "PM2.5": {"concentration": 12},
        },
        "timestamp": "2025-01-15T13:00:00",
    }
    # Fallback is unavailable
    api.async_get_aqi_fallback.return_value = None

    coordinator = MontrealAQICoordinator(
        hass=hass,
        api=api,
        station_id="80",
    )

    with pytest.raises(UpdateFailed) as exc_info:
        await coordinator._async_update_data()

    assert "Insufficient pollutant data" in str(exc_info.value)
    assert "1 pollutants" in str(exc_info.value)


async def test_coordinator_insufficient_pollutants_two(hass: HomeAssistant) -> None:
    """Test coordinator rejects data with only 2 pollutants (sensor malfunction)."""
    api = AsyncMock()
    api.async_get_station.return_value = {
        "aqi": 42,
        "dominant_pollutant": "PM2.5",
        "pollutants": {
            "PM2.5": {"concentration": 12},
            "NO2": {"concentration": 30},
        },
        "timestamp": "2025-01-15T13:00:00",
    }
    # Fallback is unavailable
    api.async_get_aqi_fallback.return_value = None

    coordinator = MontrealAQICoordinator(
        hass=hass,
        api=api,
        station_id="80",
    )

    with pytest.raises(UpdateFailed) as exc_info:
        await coordinator._async_update_data()

    assert "Insufficient pollutant data" in str(exc_info.value)
    assert "2 pollutants" in str(exc_info.value)


async def test_coordinator_sufficient_pollutants_three(hass: HomeAssistant) -> None:
    """Test coordinator accepts data with 3 or more pollutants."""
    api = AsyncMock()
    api.async_get_station.return_value = {
        "aqi": 42,
        "dominant_pollutant": "PM2.5",
        "pollutants": {
            "PM2.5": {"concentration": 12},
            "NO2": {"concentration": 30},
            "O3": {"concentration": 25},
        },
        "timestamp": "2025-01-15T13:00:00",
    }

    coordinator = MontrealAQICoordinator(
        hass=hass,
        api=api,
        station_id="80",
    )

    data = await coordinator._async_update_data()
    assert data["aqi"] == 42
    assert len(data["pollutants"]) == 3


async def test_coordinator_pollutants_with_null_values(hass: HomeAssistant) -> None:
    """Test coordinator counts only pollutants with non-null concentration."""
    api = AsyncMock()
    api.async_get_station.return_value = {
        "aqi": 42,
        "dominant_pollutant": "PM2.5",
        "pollutants": {
            "PM2.5": {"concentration": 12},
            "NO2": {"concentration": None},  # Null, not counted
            "O3": {"concentration": None},   # Null, not counted
            "SO2": {"concentration": 5},
        },
        "timestamp": "2025-01-15T13:00:00",
    }
    # Fallback is unavailable
    api.async_get_aqi_fallback.return_value = None

    coordinator = MontrealAQICoordinator(
        hass=hass,
        api=api,
        station_id="80",
    )

    with pytest.raises(UpdateFailed) as exc_info:
        await coordinator._async_update_data()

    # Only PM2.5 and SO2 have non-null values = 2 pollutants
    assert "2 pollutants" in str(exc_info.value)


async def test_coordinator_insufficient_pollutants_with_fallback_success(
    hass: HomeAssistant,
) -> None:
    """Test coordinator uses fallback AQI when primary data insufficient."""
    api = AsyncMock()
    api.async_get_station.return_value = {
        "aqi": 42,
        "dominant_pollutant": "PM2.5",
        "pollutants": {
            "PM2.5": {"concentration": 12},
        },
        "timestamp": "2025-01-15T13:00:00",
    }
    # Fallback returns AQI value
    api.async_get_aqi_fallback.return_value = {
        "aqi": 55,
        "dominant_pollutant": "O3",
    }

    coordinator = MontrealAQICoordinator(
        hass=hass,
        api=api,
        station_id="80",
    )

    data = await coordinator._async_update_data()
    # Should use fallback AQI instead of rejecting
    assert data["aqi"] == 55
    assert data["dominant_pollutant"] == "O3"
    # Fallback was called due to insufficient primary data
    api.async_get_aqi_fallback.assert_called_once_with("80")


async def test_coordinator_insufficient_pollutants_fallback_unavailable(
    hass: HomeAssistant,
) -> None:
    """Test coordinator rejects when both primary and fallback unavailable."""
    api = AsyncMock()
    api.async_get_station.return_value = {
        "aqi": 42,
        "dominant_pollutant": "PM2.5",
        "pollutants": {
            "PM2.5": {"concentration": 12},
        },
        "timestamp": "2025-01-15T13:00:00",
    }
    # Fallback returns None (unavailable)
    api.async_get_aqi_fallback.return_value = None

    coordinator = MontrealAQICoordinator(
        hass=hass,
        api=api,
        station_id="80",
    )

    with pytest.raises(UpdateFailed) as exc_info:
        await coordinator._async_update_data()

    assert "Insufficient pollutant data" in str(exc_info.value)
    assert "Fallback AQI source also unavailable" in str(exc_info.value)
