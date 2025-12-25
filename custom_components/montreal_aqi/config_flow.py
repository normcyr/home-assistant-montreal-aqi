from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.helpers.selector import SelectOptionDict

from .api import MontrealAQIApi
from .const import CONF_STATION_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)


class MontrealAQIConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Montreal AQI integration."""

    VERSION = 1

    def __init__(self) -> None:
        self._stations: dict[str, dict[str, Any]] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            station_id = user_input[CONF_STATION_ID]
            station = self._stations[station_id]

            _LOGGER.debug(
                "Config flow: selected station %s (%s)",
                station_id,
                station["name"],
            )

            return self.async_create_entry(
                title=station["name"],
                data={CONF_STATION_ID: station_id},
            )

        api = MontrealAQIApi(self.hass)

        try:
            stations = await api.async_list_stations()
        except Exception as err:
            _LOGGER.error("Config flow: cannot fetch stations: %s", err)
            return self.async_abort(reason="cannot_connect")

        if not stations:
            return self.async_abort(reason="no_stations")

        self._stations = {s["station_id"]: s for s in stations}

        options: list[SelectOptionDict] = [
            SelectOptionDict(
                value=station_id,
                label=f"{station_id} — {station['name']}",
            )
            for station_id, station in self._stations.items()
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
