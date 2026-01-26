"""Tests for API error handling."""

from unittest.mock import AsyncMock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.montreal_aqi.api import MontrealAQIApi


async def test_api_list_stations_error(hass: HomeAssistant):
    """Test API error handling when listing stations fails."""
    api = MontrealAQIApi(hass)

    async def mock_list_stations_error(*args, **kwargs):  # noqa: ARG001
        raise RuntimeError("API connection failed")

    hass.async_add_executor_job = mock_list_stations_error

    with pytest.raises(RuntimeError, match="API connection failed"):
        await api.async_list_stations()


async def test_api_list_stations_invalid_response(hass: HomeAssistant):
    """Test API handling of invalid response type."""
    api = MontrealAQIApi(hass)

    async def mock_invalid_response(*args, **kwargs):  # noqa: ARG001
        return "not a list"

    hass.async_add_executor_job = mock_invalid_response

    result = await api.async_list_stations()
    assert result == []


async def test_api_get_station_not_found(hass: HomeAssistant):
    """Test API handling when station is not found."""
    api = MontrealAQIApi(hass)

    async def mock_station_not_found(*args, **kwargs):  # noqa: ARG001
        return None

    hass.async_add_executor_job = mock_station_not_found

    result = await api.async_get_station("999")
    assert result is None


async def test_api_get_station_error(hass: HomeAssistant):
    """Test API error handling when getting station fails."""
    api = MontrealAQIApi(hass)

    async def mock_get_station_error(*args, **kwargs):  # noqa: ARG001
        raise RuntimeError("API error")

    hass.async_add_executor_job = mock_get_station_error

    with pytest.raises(RuntimeError, match="API error"):
        await api.async_get_station("80")
