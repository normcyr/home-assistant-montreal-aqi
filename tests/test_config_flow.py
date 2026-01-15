from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant

from custom_components.montreal_aqi.const import CONF_STATION_ID, DOMAIN


@pytest.fixture
def mock_stations():
    """Return mock station data."""
    return [
        {"station_id": "80", "name": "Downtown"},
        {"station_id": "39", "name": "East"},
        {"station_id": "50", "name": "West"},
    ]


async def test_config_flow_user_step(
    hass: HomeAssistant,
    enable_custom_integrations,
) -> None:
    """Test user step of config flow."""
    with patch(
        "custom_components.montreal_aqi.config_flow.MontrealAQIApi"
    ) as mock_api_class:
        mock_api = AsyncMock()
        mock_api.async_list_stations.return_value = [
            {"station_id": "80", "name": "Downtown"},
        ]
        mock_api_class.return_value = mock_api

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )

        assert result["type"] == "form"
        assert result["step_id"] == "user"


async def test_config_flow_success(
    hass: HomeAssistant,
    enable_custom_integrations,
    mock_stations: list,
) -> None:
    """Test successful config flow."""
    with patch(
        "custom_components.montreal_aqi.config_flow.MontrealAQIApi"
    ) as mock_api_class:
        mock_api = AsyncMock()
        mock_api.async_list_stations.return_value = mock_stations
        mock_api_class.return_value = mock_api

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )

        assert result["type"] == "form"
        assert result["step_id"] == "user"

        # Submit form with station selection
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_STATION_ID: "80"},
        )

        assert result["type"] == "create_entry"
        assert result["title"] == "Downtown"
        assert result["data"] == {CONF_STATION_ID: "80"}


async def test_config_flow_duplicate_station(
    hass: HomeAssistant,
    enable_custom_integrations,
    mock_stations: list,
) -> None:
    """Test config flow prevents duplicate station."""
    # Pre-configure station 80
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.montreal_aqi.const import DOMAIN

    existing_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Station 80",
        data={CONF_STATION_ID: "80"},
        unique_id="80",
    )
    existing_entry.add_to_hass(hass)

    with patch(
        "custom_components.montreal_aqi.config_flow.MontrealAQIApi"
    ) as mock_api_class:
        mock_api = AsyncMock()
        mock_api.async_list_stations.return_value = mock_stations
        mock_api_class.return_value = mock_api

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_STATION_ID: "80"},
        )

        # Should abort with unique_id already configured
        assert result["type"] == "abort"
        assert result["reason"] == "already_configured"


async def test_config_flow_api_error(
    hass: HomeAssistant,
    enable_custom_integrations,
) -> None:
    """Test config flow handles API errors."""
    with patch(
        "custom_components.montreal_aqi.config_flow.MontrealAQIApi"
    ) as mock_api_class:
        mock_api = AsyncMock()
        mock_api.async_list_stations.side_effect = Exception("API error")
        mock_api_class.return_value = mock_api

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )

        assert result["type"] == "abort"
        assert result["reason"] == "cannot_connect"


async def test_config_flow_no_stations(
    hass: HomeAssistant,
    enable_custom_integrations,
) -> None:
    """Test config flow when no stations available."""
    with patch(
        "custom_components.montreal_aqi.config_flow.MontrealAQIApi"
    ) as mock_api_class:
        mock_api = AsyncMock()
        mock_api.async_list_stations.return_value = []
        mock_api_class.return_value = mock_api

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )

        assert result["type"] == "abort"
        assert result["reason"] == "no_stations"


async def test_config_flow_stations_sorted(
    hass: HomeAssistant,
    enable_custom_integrations,
) -> None:
    """Test stations are sorted by numeric ID."""
    with patch(
        "custom_components.montreal_aqi.config_flow.MontrealAQIApi"
    ) as mock_api_class:
        mock_api = AsyncMock()
        # Return unsorted stations
        mock_api.async_list_stations.return_value = [
            {"station_id": "50", "name": "West"},
            {"station_id": "80", "name": "Downtown"},
            {"station_id": "39", "name": "East"},
        ]
        mock_api_class.return_value = mock_api

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )

        # Check that form schema has sorted options
        schema = result["data_schema"]
        options = schema.schema[CONF_STATION_ID].config["options"]
        # Options are SelectOptionDict, access value attribute
        values = [opt["value"] for opt in options]

        # Should be sorted: 39, 50, 80
        assert values == ["39", "50", "80"]
