import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from pytest_homeassistant_custom_component.common import MockConfigEntry

# Mock montreal_aqi_api BEFORE importing custom_components
sys.modules["montreal_aqi_api"] = MagicMock()

from custom_components.montreal_aqi.const import CONF_STATION_ID, DOMAIN

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))


@pytest.fixture
def mock_config_entry(hass: HomeAssistant) -> ConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Station 80",
        data={CONF_STATION_ID: "80"},
        unique_id="station_80",
    )

    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def mock_station_data():
    return {
        "aqi": 42,
        "dominant_pollutant": "PM2.5",
        "pollutants": {
            "PM2.5": {"concentration": 12},
            "NO2": {"concentration": 18},
            "O3": {"concentration": 25},
        },
        "timestamp": "2025-01-15T13:00:00",
    }


@pytest.fixture
def mock_api():
    api = AsyncMock()
    api.async_get_station.return_value = {
        "aqi": 10,
        "dominant_pollutant": "PM2.5",
        "pollutants": {},
        "timestamp": "2025-01-15T13:00:00",
    }
    return api


@pytest.fixture
def device_info():
    def _make(station_id: str):
        return DeviceInfo(
            identifiers=("montreal_aqi", station_id),
            name=f"Station {station_id}",
            manufacturer="Ville de Montréal",
            model="Air Quality Station",
        )

    return _make
