from unittest.mock import AsyncMock

from custom_components.montreal_aqi.air_quality import MontrealAQIAirQualityEntity


async def test_air_quality_basic_state(hass, mock_config_entry):
    coordinator = AsyncMock()
    coordinator.last_update_success = True
    coordinator.data = {
        "aqi": 30,
        "dominant_pollutant": "PM2.5",
        "pollutants": {
            "PM2.5": {"concentration": 11.2},
            "NO2": {"concentration": 22},
        },
    }

    entity = MontrealAQIAirQualityEntity(
        coordinator=coordinator,
        entry=mock_config_entry,
    )

    assert entity.available is True
    assert entity.air_quality_index == 30
    assert entity.state == "Acceptable"


async def test_air_quality_state_good(hass, mock_config_entry):
    coordinator = AsyncMock()
    coordinator.last_update_success = True
    coordinator.data = {"aqi": 10}

    entity = MontrealAQIAirQualityEntity(coordinator, mock_config_entry)

    assert entity.state == "Good"


async def test_air_quality_state_bad(hass, mock_config_entry):
    coordinator = AsyncMock()
    coordinator.last_update_success = True
    coordinator.data = {"aqi": 75}

    entity = MontrealAQIAirQualityEntity(coordinator, mock_config_entry)

    assert entity.state == "Bad"


async def test_air_quality_attributes(hass, mock_config_entry):
    coordinator = AsyncMock()
    coordinator.last_update_success = True
    coordinator.data = {
        "aqi": 42,
        "dominant_pollutant": "NO2",
        "pollutants": {
            "NO2": {"concentration": 18},
        },
    }

    entity = MontrealAQIAirQualityEntity(coordinator, mock_config_entry)

    attrs = entity.extra_state_attributes

    assert attrs["air quality"] == "Acceptable"
    assert attrs["air quality index"] == 42
    assert attrs["dominant_pollutant"] == "NO2"


async def test_missing_pollutant_returns_none(hass, mock_config_entry):
    coordinator = AsyncMock()
    coordinator.last_update_success = True
    coordinator.data = {
        "aqi": 35,
        "pollutants": {
            "PM2.5": {"concentration": 9.5},
        },
    }

    entity = MontrealAQIAirQualityEntity(coordinator, mock_config_entry)

    # Polluant présent
    assert entity.particulate_matter_2_5 == 9.5

    # Polluants absents → None (donc NON affichés)
    assert entity.carbon_monoxide is None
    assert entity.nitrogen_dioxide is None
    assert entity.ozone is None
    assert entity.sulphur_dioxide is None


async def test_no_pollutants_key(hass, mock_config_entry):
    coordinator = AsyncMock()
    coordinator.last_update_success = True
    coordinator.data = {"aqi": 20}

    entity = MontrealAQIAirQualityEntity(coordinator, mock_config_entry)

    assert entity.particulate_matter_2_5 is None
    assert entity.carbon_monoxide is None
