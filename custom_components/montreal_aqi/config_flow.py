from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_STATION_ID
from .api import MontrealAQIClient


class MontrealAQIConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            station_id = user_input[CONF_STATION_ID]

            client = MontrealAQIClient(station_id)
            station = await self.hass.async_add_executor_job(client.fetch_station)

            if station is None:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(station_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Montreal AQI ({station_id})",
                    data={CONF_STATION_ID: station_id},
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_STATION_ID): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )


# import logging

# import voluptuous as vol
# from homeassistant import config_entries

# from .api import get_list_stations
# from .const import CONF_STATION, DOMAIN

# _LOGGER = logging.getLogger(__name__)


# class MontrealAQIConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
#     """Handle the config flow for Montreal AQI integration."""

#     async def async_step_user(self, user_input=None):
#         """Handle the initial user input."""
#         errors = {}

#         try:
#             # Fetch the list of stations
#             list_stations = await get_list_stations()
#             if not list_stations:
#                 return self.async_abort(reason="no_stations")

#             # Convert station list into a dictionary for selection
#             station_options = {
#                 station[
#                     "station_id"
#                 ]: f"Station {station['station_id']} - {station['station_name']} ({station['station_borough']})"
#                 for station in list_stations
#             }

#         except Exception as e:
#             self.hass.helpers.event.log_error(f"Error fetching stations: {e}")
#             return self.async_abort(reason="api_error")

#         # Ensure station_options exists before handling user input
#         if user_input is not None:
#             _LOGGER.info(station_options)
#             selected_station_name = user_input[CONF_STATION]

#             # Look for the selected station name and retrieve the corresponding station ID
#             selected_station_id = next(
#                 (
#                     station_id
#                     for station_id, name in station_options.items()
#                     if name == selected_station_name
#                 ),
#                 None,
#             )

#             if selected_station_id is None:
#                 errors["base"] = "invalid_station"
#             else:
#                 return self.async_create_entry(
#                     title=selected_station_name,
#                     data={"station_id": selected_station_id},
#                 )

#         return self.async_show_form(
#             step_id="user",
#             data_schema=vol.Schema(
#                 {vol.Required(CONF_STATION): vol.In(list(station_options.values()))}
#             ),
#             errors=errors,
#         )
