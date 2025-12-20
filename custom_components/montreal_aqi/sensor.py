from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]

    station = coordinator.data

    entities: list[SensorEntity] = []

    # AQI global
    entities.append(MontrealAQIGlobalSensor(coordinator))

    # Pollutants
    for code in station.pollutants.keys():
        entities.append(MontrealAQIPollutantAQISensor(coordinator, code))
        entities.append(MontrealAQIPollutantConcentrationSensor(coordinator, code))

    async_add_entities(entities)


class MontrealAQIBaseSensor(SensorEntity):
    def __init__(self, coordinator):
        self.coordinator = coordinator

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    async def async_update(self) -> None:
        await self.coordinator.async_request_refresh()


class MontrealAQIGlobalSensor(MontrealAQIBaseSensor):
    _attr_name = "Montreal AQI"
    _attr_icon = "mdi:weather-hazy"

    @property
    def unique_id(self) -> str:
        return f"{self.coordinator.data.station_id}_aqi"

    @property
    def native_value(self) -> int:
        return self.coordinator.data.aqi

    @property
    def extra_state_attributes(self):
        return {
            "station_id": self.coordinator.data.station_id,
            "dominant_pollutant": self.coordinator.data.main_pollutant.name,
            "date": self.coordinator.data.date.isoformat(),
            "hour": self.coordinator.data.hour,
        }


class MontrealAQIPollutantAQISensor(MontrealAQIBaseSensor):
    def __init__(self, coordinator, code: str):
        super().__init__(coordinator)
        self.code = code

    @property
    def name(self) -> str:
        return f"{self.code.upper()} AQI"

    @property
    def unique_id(self) -> str:
        return f"{self.coordinator.data.station_id}_{self.code}_aqi"

    @property
    def native_value(self) -> int:
        return self.coordinator.data.pollutants[self.code].aqi


class MontrealAQIPollutantConcentrationSensor(MontrealAQIBaseSensor):
    def __init__(self, coordinator, code: str):
        super().__init__(coordinator)
        self.code = code

    @property
    def name(self) -> str:
        return f"{self.code.upper()} concentration"

    @property
    def unique_id(self) -> str:
        return f"{self.coordinator.data.station_id}_{self.code}_concentration"

    @property
    def native_value(self) -> float:
        return self.coordinator.data.pollutants[self.code].concentration

    @property
    def native_unit_of_measurement(self) -> str:
        return "µg/m³"


# import logging
# from datetime import timedelta

# import aiohttp
# from homeassistant.components.sensor import SensorEntity
# from homeassistant.helpers.entity import DeviceInfo
# from homeassistant.helpers.update_coordinator import (
#     CoordinatorEntity,
#     DataUpdateCoordinator,
#     UpdateFailed,
# )

# from .api import MontrealAQIAPI
# from .const import DOMAIN, POLLUTANT_UNITS, POLLUTANTS, UPDATE_INTERVAL

# _LOGGER = logging.getLogger(__name__)


# async def async_setup_entry(hass, entry, async_add_entities):
#     """Set up sensors based on the config entry."""
#     station_id = entry.data["station_id"]
#     session = aiohttp.ClientSession()
#     api = MontrealAQIAPI(session, station_id)

#     async def async_update_data():
#         """Fetch the latest AQI and pollutant data from the API."""
#         data = await api.get_latest_data()
#         if not data:
#             raise UpdateFailed("Failed to fetch AQI data")
#         return data

#     coordinator = DataUpdateCoordinator(
#         hass,
#         _LOGGER,
#         name=f"Montreal AQI {station_id}",
#         update_method=async_update_data,
#         update_interval=timedelta(seconds=UPDATE_INTERVAL),
#     )

#     await coordinator.async_config_entry_first_refresh()

#     # Create the device (station) with all sensors linked to it
#     device_info = DeviceInfo(
#         identifiers={(DOMAIN, station_id)},
#         name=f"Montreal Air Quality Monitoring Station {station_id}",
#         manufacturer="Réseau de surveillance de la qualité de l'air",
#         model="Air Quality Sensor",
#         entry_type="service",
#         configuration_url="https://donnees.montreal.ca/",
#     )

#     sensors = [
#         AQISensor(coordinator, station_id, device_info),
#         AirQualityCategorySensor(coordinator, station_id, device_info),
#     ]

#     for pollutant in POLLUTANTS:
#         if pollutant in coordinator.data:
#             sensors.append(
#                 PollutantSensor(coordinator, station_id, pollutant, device_info)
#             )

#     async_add_entities(sensors, True)


# class AQISensor(CoordinatorEntity, SensorEntity):
#     """AQI sensor entity."""

#     def __init__(self, coordinator, station_id, device_info):
#         super().__init__(coordinator)
#         self.station_id = station_id
#         self._attr_name = f"AQI Station {station_id}"
#         self._attr_unique_id = f"montreal_aqi_station_{station_id}"
#         self._attr_device_class = "aqi"
#         self._attr_unit_of_measurement = "AQI"
#         self._attr_suggested_display_precision = 0
#         self._attr_device_info = device_info
#         self._attr_state_class = "measurement"

#         _LOGGER.debug("Initialized Air Quality Sensor for station %s", station_id)

#     @property
#     def state(self):
#         """Return the AQI value from the coordinator data."""
#         aqi = self.coordinator.data.get("AQI")
#         if aqi is None:
#             _LOGGER.warning("No AQI data available for station %s", self.station_id)
#         return aqi


# class PollutantSensor(CoordinatorEntity, SensorEntity):
#     """Pollutant level sensor."""

#     def __init__(self, coordinator, station_id, pollutant, device_info):
#         super().__init__(coordinator)
#         self.pollutant = pollutant
#         self.station_id = station_id
#         self._attr_name = f"{pollutant} level station {station_id}"
#         self._attr_unique_id = f"{pollutant.lower()}_montreal_aqi_station_{station_id}"
#         _LOGGER.debug(
#             "Initialized Pollutant Sensor for %s at station %s", pollutant, station_id
#         )

#         device_classes = {
#             "CO": "carbon_monoxide",
#             "SO2": "sulphur_dioxide",
#             "O3": "ozone",
#             "NO2": "nitrogen_dioxide",
#             "PM": "pm25",
#         }
#         self._attr_device_class = device_classes.get(pollutant, "aqi")

#         self._attr_unit_of_measurement = POLLUTANT_UNITS.get(pollutant, "")
#         self._attr_device_info = device_info
#         self._attr_suggested_display_precision = 0

#         _LOGGER.debug(
#             f"Pollutant {pollutant} assigned unit: {self._attr_unit_of_measurement}"
#         )

#     @property
#     def state(self):
#         """Return the pollutant level from the coordinator data."""
#         pollutant_value = self.coordinator.data.get(self.pollutant)
#         if pollutant_value is None:
#             _LOGGER.warning(
#                 "No data available for pollutant %s at station %s",
#                 self.pollutant,
#                 self.station_id,
#             )
#             return None
#         else:
#             _LOGGER.debug(
#                 "Pollutant %s at station %s state value: %s",
#                 self.pollutant,
#                 self.station_id,
#                 pollutant_value,
#             )
#         return pollutant_value

#     @property
#     def unit_of_measurement(self):
#         return POLLUTANT_UNITS.get(self.pollutant, "")


# class AirQualityCategorySensor(CoordinatorEntity, SensorEntity):
#     """Air quality category sensor entity based on AQI values."""

#     def __init__(self, coordinator, station_id, device_info):
#         super().__init__(coordinator)
#         self.station_id = station_id
#         self._attr_name = f"Air Quality Category Station {station_id}"
#         self._attr_unique_id = f"air_quality_category_station_{station_id}"
#         self._attr_device_class = None
#         self._attr_device_info = device_info
#         self._attr_icon = "mdi:cloud-alert"
#         _LOGGER.debug("Initialized Air category sensor for station %s", station_id)

#     @property
#     def state(self):
#         """Return the air quality category based on AQI value."""
#         aqi = self.coordinator.data.get("AQI")
#         _LOGGER.debug(f"Current AQI value: {aqi}")
#         if aqi is not None:
#             if aqi <= 25:
#                 return "Good"
#             elif 26 <= aqi <= 50:
#                 return "Acceptable"
#             else:
#                 return "Bad"
#         return None
