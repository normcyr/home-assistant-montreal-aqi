from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector
from homeassistant.helpers.selector import SelectOptionDict

from .api import MontrealAQIApi
from .const import CONF_STATION_ID, DOMAIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigFlowResult

_LOGGER = logging.getLogger(__name__)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidStation(HomeAssistantError):
    """Error to indicate invalid station."""


class MontrealAQIConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for Montreal AQI integration."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self._stations: dict[str, dict[str, Any]] = {}

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        if user_input is not None:
            station_id = user_input[CONF_STATION_ID]
            station = self._stations.get(station_id)

            if not station:
                _LOGGER.error(
                    "Config flow: station %s not found in available stations",
                    station_id,
                )
                return self.async_abort(reason="invalid_station")

            # Check if already configured
            await self.async_set_unique_id(station_id)
            self._abort_if_unique_id_configured()

            _LOGGER.debug(
                "Config flow: selected station %s (%s)",
                station_id,
                station.get("name", "Unknown"),
            )

            return self.async_create_entry(
                title=station.get("name", station_id),
                data={CONF_STATION_ID: station_id},
            )

        api = MontrealAQIApi(self.hass)

        try:
            stations = await api.async_list_stations()
        except Exception as err:
            _LOGGER.error(
                "Config flow: cannot fetch stations: %s",
                err,
                exc_info=True,
            )
            return self.async_abort(reason="cannot_connect")

        if not stations:
            _LOGGER.warning("Config flow: no stations available from API")
            return self.async_abort(reason="no_stations")

        self._stations = {s["station_id"]: s for s in stations}

        # Sort stations by station_id (numeric) for consistent ordering
        options: list[SelectOptionDict] = [
            SelectOptionDict(
                value=station_id,
                label=f"{station_id} — {station.get('name', 'Unknown')}",
            )
            for station_id, station in sorted(
                self._stations.items(),
                key=lambda item: int(item[0]) if str(item[0]).isdigit() else item[0],
            )
        ]

        _LOGGER.debug("Config flow: presenting %d stations", len(options))

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STATION_ID): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
        )
