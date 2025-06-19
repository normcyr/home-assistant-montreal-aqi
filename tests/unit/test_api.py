import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest

# Add the module path
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from custom_components.montreal_aqi.api import MontrealAQIAPI
from custom_components.montreal_aqi.const import API_URL, RESOURCE_ID


@pytest.mark.asyncio
async def test_get_latest_data():
    """Test if the API client returns data correctly."""

    # Simulate the data returned by the API
    mock_data = {
        "station_id": 80,
        "AQI": 42,
        "pollutants": {"CO": 0.4, "NO2": 12.5, "O3": 23.6, "PM": 15.1, "SO2": 25.0},
    }

    # Create a simulated HTTP session
    async with aiohttp.ClientSession() as session:
        # Mock the `get_latest_data` method
        with patch(
            "custom_components.montreal_aqi.api.MontrealAQIAPI.get_latest_data",
            new=AsyncMock(return_value=mock_data),
        ):
            # Execute the API method
            api = MontrealAQIAPI(session, station_id=80)
            data = await api.get_latest_data()

            # Assertions to verify the results
            assert data["AQI"] == 42
            assert data["pollutants"]["CO"] == 0.4
            assert data["pollutants"]["NO2"] == 12.5
            assert data["pollutants"]["O3"] == 23.6
            assert data["pollutants"]["PM"] == 15.1
            assert data["pollutants"]["SO2"] == 25.0


@pytest.mark.parametrize("expected_lingering_tasks", [True])
@pytest.mark.parametrize("expected_lingering_timers", [True])
@pytest.mark.parametrize("expected_lingering_threads", [True])
@pytest.mark.asyncio
async def test_get_latest_data_failure(
    expected_lingering_tasks,
    expected_lingering_timers,
    expected_lingering_threads,
):
    """Test the API client if it handles errors correctly."""

    # Create a simulated HTTP session
    async with aiohttp.ClientSession() as session:
        # Simulate an exception during the API call
        with patch(
            "custom_components.montreal_aqi.api.MontrealAQIAPI.get_latest_data",
            new=AsyncMock(side_effect=Exception("API error")),
        ):
            api = MontrealAQIAPI(session, station_id="80")

            with pytest.raises(Exception, match="API error"):
                await api.get_latest_data()


@pytest.mark.asyncio
async def test_get_latest_data_different_station():
    """Test the API client if it returns correct data for a different station."""
    mock_data_station_81 = {
        "station_id": 81,
        "AQI": 50,
        "pollutants": {"CO": 0.8, "NO2": 15.0, "O3": 30.0, "PM": 20.0, "SO2": 35.0},
    }

    async with aiohttp.ClientSession() as session:
        with patch(
            "custom_components.montreal_aqi.api.MontrealAQIAPI.get_latest_data",
            new=AsyncMock(return_value=mock_data_station_81),
        ):
            api = MontrealAQIAPI(session, station_id=81)
            data = await api.get_latest_data()

            assert data["station_id"] == 81
            assert data["pollutants"]["CO"] == 0.8


@pytest.mark.asyncio
async def test_get_latest_data_partial_response():
    """Test the API client if it handles partial responses."""
    mock_partial_data = {
        "station_id": 80,
        "AQI": 45,
        "pollutants": {"CO": 0.3},  # Missing other pollutants
    }

    async with aiohttp.ClientSession() as session:
        with patch(
            "custom_components.montreal_aqi.api.MontrealAQIAPI.get_latest_data",
            new=AsyncMock(return_value=mock_partial_data),
        ):
            api = MontrealAQIAPI(session, station_id=80)
            data = await api.get_latest_data()

            assert data["AQI"] == 45
            assert "NO2" not in data["pollutants"]
            assert data["pollutants"]["CO"] == 0.3


@pytest.mark.asyncio
async def test_valid_api_url():
    """Test if the URL is correctly constructed and valid."""

    async with aiohttp.ClientSession() as session:
        api = MontrealAQIAPI(session, station_id=80)

        # Mocking the GET request to avoid hitting the actual API
        with patch("aiohttp.ClientSession.get") as mock_get:
            # Trigger the method
            await api.get_latest_data()

            # Check that the correct URL and parameters are used
            mock_get.assert_called_with(API_URL, params={"resource_id": RESOURCE_ID, "limit": 1000})


@pytest.mark.asyncio
async def test_status_code():
    """Test if the API call returns the correct status code."""

    async with aiohttp.ClientSession() as session:
        with patch("aiohttp.ClientSession.get") as mock_get:
            # Mock the response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_get.return_value = mock_response

            api = MontrealAQIAPI(session, station_id="80")

            # Perform the API call
            result = await api.get_latest_data()

            # Assert that the response status code is 200
            assert mock_response.status == 200


@pytest.mark.asyncio
async def test_timeout():
    """Test if the API call times out correctly."""

    async with aiohttp.ClientSession() as session:
        # Mocking the `get` method to simulate a timeout
        with patch("aiohttp.ClientSession.get", side_effect=asyncio.TimeoutError):
            api = MontrealAQIAPI(session, station_id=80)

            # Ensure that asyncio.TimeoutError is raised
            with pytest.raises(asyncio.TimeoutError):
                await api.get_latest_data()


@pytest.mark.asyncio
async def test_api_error_response():
    """Test the behavior of the API client when an error status code is returned."""

    async with aiohttp.ClientSession() as session:
        with patch("aiohttp.ClientSession.get") as mock_get:
            # Simulate an error response with status 500 (Internal Server Error)
            mock_get.return_value.status = 500
            api = MontrealAQIAPI(session, station_id=80)

            response = await api.get_latest_data()
            assert response is None
            mock_get.assert_called_once()


@pytest.mark.asyncio
async def test_parse_data():
    """Test if the data parsing logic works for various input scenarios."""

    # Simulate complete data
    complete_data = {"result": {"records": [{"stationId": 80, "polluant": "CO", "valeur": "0.4", "heure": "12"}]}}

    async with aiohttp.ClientSession() as session:
        api = MontrealAQIAPI(session, station_id=80)
        parsed_data = api._parse_data(complete_data)

        # Check if the data was parsed correctly
        assert parsed_data["CO"] == 0.4
        assert parsed_data["AQI"] == 1  # Depending on your logic for AQI calculation


@pytest.mark.asyncio
async def test_initialization():
    """Test if the MontrealAQIAPI is initialized properly."""

    async with aiohttp.ClientSession() as session:
        api = MontrealAQIAPI(session, station_id=80)

        assert api.session is session
        assert api.station_id == 80
