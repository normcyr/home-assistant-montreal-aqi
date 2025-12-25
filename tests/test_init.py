from unittest.mock import AsyncMock, patch

from custom_components.montreal_aqi.const import DOMAIN

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant


async def test_async_setup_entry(
    hass: HomeAssistant,
    mock_config_entry,
    mock_api: AsyncMock,
    enable_custom_integrations,
) -> None:
    """Test async setup entry."""

    mock_config_entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.montreal_aqi.api.MontrealAQIApi",
            return_value=mock_api,
        ),
        patch(
            "custom_components.montreal_aqi.coordinator.MontrealAQICoordinator.async_config_entry_first_refresh",
            return_value=None,
        ) as refresh,
        patch(
            "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups"
        ) as forward,
    ):
        result = await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert result is True
    assert mock_config_entry.state is ConfigEntryState.LOADED

    refresh.assert_called_once()
    forward.assert_called_once_with(
        mock_config_entry,
        ["air_quality", "sensor"],
    )


async def test_async_unload_entry(
    hass: HomeAssistant,
    enable_custom_integrations,
    mock_config_entry,
):
    """Test unloading a config entry."""
    mock_config_entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.montreal_aqi.MontrealAQICoordinator.async_config_entry_first_refresh"
        ),
        patch(
            "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
            return_value=True,
        ),
        patch(
            "homeassistant.config_entries.ConfigEntries.async_unload_platforms",
            return_value=True,
        ),
    ):
        # Setup réel
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert mock_config_entry.state is ConfigEntryState.LOADED
        assert mock_config_entry.entry_id in hass.data[DOMAIN]

        # Unload réel
        assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert mock_config_entry.state is ConfigEntryState.NOT_LOADED
        assert mock_config_entry.entry_id not in hass.data.get(DOMAIN, {})


async def test_reload_entry(
    hass: HomeAssistant,
    enable_custom_integrations,
    mock_config_entry,
):
    """Test reload of a config entry."""
    mock_config_entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.montreal_aqi.MontrealAQICoordinator.async_config_entry_first_refresh"
        ),
        patch(
            "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
            return_value=True,
        ),
        patch(
            "homeassistant.config_entries.ConfigEntries.async_unload_platforms",
            return_value=True,
        ),
    ):
        # Setup initial
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert mock_config_entry.state is ConfigEntryState.LOADED
        assert mock_config_entry.entry_id in hass.data[DOMAIN]

        # Reload
        assert await hass.config_entries.async_reload(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Toujours chargé après reload
        assert mock_config_entry.state is ConfigEntryState.LOADED
        assert mock_config_entry.entry_id in hass.data[DOMAIN]


async def test_setup_entry_failure(
    hass: HomeAssistant,
    enable_custom_integrations,
    mock_config_entry,
):
    """Test setup entry failure."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.montreal_aqi.MontrealAQICoordinator.async_config_entry_first_refresh",
        side_effect=Exception("API error"),
    ):
        result = await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert result is False
    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR

    assert DOMAIN not in hass.data
