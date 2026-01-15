from unittest.mock import AsyncMock

from custom_components.montreal_aqi.coordinator import MontrealAQICoordinator


async def test_coordinator_update(hass, mock_station_data):
    api = AsyncMock()
    api.async_get_station.return_value = mock_station_data

    coordinator = MontrealAQICoordinator(
        hass=hass,
        api=api,
        station_id=80,
    )

    data = await coordinator._async_update_data()

    assert data["aqi"] == 42
    assert data["dominant_pollutant"] == "PM2.5"
    assert "NO2" in data["pollutants"]
    assert data["pollutants"]["PM2.5"]["concentration"] == 12
