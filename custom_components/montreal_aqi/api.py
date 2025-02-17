import asyncio
import logging

import aiohttp
import async_timeout

from .const import API_URL, LIST_RESOURCE_ID, REF_VALUES, RESOURCE_ID

_LOGGER = logging.getLogger(__name__)


class Pollutant:
    """Represents an air pollutant with AQI calculation."""

    def __init__(self, name: str, ref_value: int):
        self.name = name
        self.ref_value = ref_value
        self.value = 0
        self.aqi_value = 0

    def set_value(self, value: float):
        """Set the pollutant concentration."""
        self.value = float(value)
        _LOGGER.debug(f"Set {self.name} value to {self.value}")

    def calculate_aqi(self):
        """Calculate AQI contribution using AQI = (value / ref_value) * 50."""
        self.aqi_value = (self.value / self.ref_value) * 50 if self.ref_value else 0
        _LOGGER.debug(f"Calculated AQI for {self.name}: {self.aqi_value}")


class MontrealAQIAPI:
    """Async API wrapper for Montreal's Air Quality data."""

    def __init__(self, session: aiohttp.ClientSession, station_id: str):
        self.session = session
        self.station_id = station_id
        _LOGGER.debug(f"Initialized MontrealAQI API for station {station_id}")

    async def get_latest_data(self):
        """Fetch latest AQI data for a given station."""
        params = {"resource_id": RESOURCE_ID, "limit": 1000}
        _LOGGER.debug(
            f"Fetching latest AQI data for station {self.station_id} with params {params}"
        )
        try:
            async with async_timeout.timeout(10):
                async with self.session.get(API_URL, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data:
                            _LOGGER.debug("Fetched data: %s", data)
                            return self._parse_data(data)
                        else:
                            _LOGGER.warning("No air quality data available")
                            return None
                    else:
                        _LOGGER.error(
                            "API request failed with status code %s", response.status
                        )
                        return None
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            _LOGGER.error("Error fetching AQI data: %s", str(e))
            raise

    def _parse_data(self, data):
        """Extract latest AQI and pollutant data for the station."""
        records = data.get("result", {}).get("records", [])
        filtered_data = [r for r in records if r.get("stationId") == self.station_id]

        if not filtered_data:
            _LOGGER.warning("No data found for station %s", self.station_id)
            return None

        # Find latest hour
        latest_hour = max(int(entry["heure"]) for entry in filtered_data)
        _LOGGER.debug(f"Latest hour found for station {self.station_id}: {latest_hour}")

        # Filter only the latest records
        latest_data = [r for r in filtered_data if int(r["heure"]) == latest_hour]

        pollutants = {
            "SO2": Pollutant("SO2", REF_VALUES["SO2"]),
            "CO": Pollutant("CO", REF_VALUES["CO"]),
            "O3": Pollutant("O3", REF_VALUES["O3"]),
            "NO2": Pollutant("NO2", REF_VALUES["NO2"]),
            "PM": Pollutant("PM", REF_VALUES["PM"]),
        }

        for entry in latest_data:
            pollutant_name = entry["polluant"]
            value = float(entry["valeur"])

            if pollutant_name in pollutants:
                pollutants[pollutant_name].set_value(value)
                pollutants[pollutant_name].calculate_aqi()
            else:
                _LOGGER.warning(
                    "Unknown pollutant %s received from API", pollutant_name
                )

        # Calculate total AQI
        total_aqi = round(sum(p.aqi_value for p in pollutants.values()), 0)
        _LOGGER.debug(f"Total AQI calculated: {total_aqi}")

        return {
            "AQI": total_aqi,
            "SO2": pollutants["SO2"].value,
            "CO": pollutants["CO"].value,
            "O3": pollutants["O3"].value,
            "NO2": pollutants["NO2"].value,
            "PM": pollutants["PM"].value,
        }


async def get_list_stations():
    params = {"resource_id": LIST_RESOURCE_ID}
    _LOGGER.info("Fetching list of monitoring stations...")

    async with aiohttp.ClientSession() as session:
        try:
            logging.info("Fetching list of monitoring stations...")
            async with session.get(API_URL, params=params) as response:
                response.raise_for_status()

                if response.status == 200:
                    data = await response.json()
                    records = data.get("result", {}).get("records", [])
                    list_stations = []

                    for record in records:
                        if record["statut"] == "ouvert":
                            station_info = {
                                "station_id": record["numero_station"],
                                "station_name": record["nom"],
                                "station_address": record["adresse"],
                                "station_borough": record["arrondissement_ville"],
                            }
                            _LOGGER.debug("Adding station info: %s", station_info)
                            list_stations.append(station_info)

                    _LOGGER.info("Found a list of monitoring stations.")
                    _LOGGER.debug(f"List of stations: {list_stations}")
                    return list_stations
                else:
                    _LOGGER.error(f"API Error: {response.status}")
                    return None
        except aiohttp.ClientError as e:
            _LOGGER.error(f"Request failed: {e}")
            return None
