from unittest.mock import AsyncMock

from custom_components.montreal_aqi.const import AQI_LEVEL_DESCRIPTION
from custom_components.montreal_aqi.sensor import MontrealAQISensor


async def test_aqi_enum_good(hass, mock_config_entry):
    coordinator = AsyncMock()
    coordinator.last_update_success = True
    coordinator.data = {"aqi": 20}

    sensor = MontrealAQISensor(
        coordinator=coordinator,
        entry=mock_config_entry,
        description=AQI_LEVEL_DESCRIPTION,
    )

    assert sensor.native_value == "Good"


async def test_aqi_enum_acceptable(hass, mock_config_entry):
    coordinator = AsyncMock()
    coordinator.last_update_success = True
    coordinator.data = {"aqi": 40}

    sensor = MontrealAQISensor(
        coordinator=coordinator,
        entry=mock_config_entry,
        description=AQI_LEVEL_DESCRIPTION,
    )

    assert sensor.native_value == "Acceptable"


async def test_aqi_enum_bad(hass, mock_config_entry):
    coordinator = AsyncMock()
    coordinator.last_update_success = True
    coordinator.data = {"aqi": 80}

    sensor = MontrealAQISensor(
        coordinator=coordinator,
        entry=mock_config_entry,
        description=AQI_LEVEL_DESCRIPTION,
    )

    assert sensor.native_value == "Bad"
