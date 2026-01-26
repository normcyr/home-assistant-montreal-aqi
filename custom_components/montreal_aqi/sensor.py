from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (
    CONF_STATION_ID,
    DEVICE_CLASS_MAP,
    DOMAIN,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import MontrealAQICoordinator

_LOGGER = logging.getLogger(__name__)


# -------------------------------------------------------------------
# Setup
# -------------------------------------------------------------------


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Montreal AQI sensors from config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry
        async_add_entities: Callback to add entities
    """
    coordinator: MontrealAQICoordinator = hass.data[DOMAIN][entry.entry_id]
    station_id: str = entry.data[CONF_STATION_ID]

    # Device info shared by all sensors of this station
    device_info = DeviceInfo(
        identifiers={(DOMAIN, station_id)},
        name=f"Montreal AQI Station {station_id}",
        manufacturer="Ville de Montréal",
        model="Air Quality Monitoring Station",
    )

    sensors: list[SensorEntity] = [
        MontrealAQIIndexSensor(coordinator, device_info, entry.entry_id, station_id),
        MontrealAQILevelSensor(coordinator, device_info, entry.entry_id, station_id),
        MontrealAQITimestampSensor(coordinator, device_info, entry.entry_id, station_id),
    ]

    # Add pollutant sensors for available pollutants
    pollutants: dict[str, Any] = coordinator.data.get("pollutants", {})
    _LOGGER.debug(
        "Setting up sensors for station %s with pollutants: %s",
        station_id,
        list(pollutants.keys()),
    )

    for code, meta in DEVICE_CLASS_MAP.items():
        if code not in pollutants:
            _LOGGER.debug("Pollutant %s not available for station %s", code, station_id)
            continue

        _LOGGER.debug("Adding pollutant sensor for %s (station %s)", code, station_id)
        sensors.append(
            MontrealAQIPollutantSensor(
                coordinator=coordinator,
                device_info=device_info,
                entry_id=entry.entry_id,
                station_id=station_id,
                code=code,
                meta=meta,
            )
        )

    _LOGGER.debug("Setting up %d sensors for station %s", len(sensors), station_id)
    async_add_entities(sensors, update_before_add=True)


# -------------------------------------------------------------------
# Base entity
# -------------------------------------------------------------------


class MontrealAQIBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for Montreal AQI sensors."""

    _attr_should_poll = False

    def __init__(
        self,
        coordinator: MontrealAQICoordinator,
        device_info: DeviceInfo,
        entry_id: str,
        station_id: str,
    ) -> None:
        """Initialize base sensor.

        Args:
            coordinator: Data coordinator
            device_info: Device information
            entry_id: Config entry ID
            station_id: Station ID
        """
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._entry_id = entry_id
        self._station_id = station_id

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success


# -------------------------------------------------------------------
# AQI index sensor
# -------------------------------------------------------------------


class MontrealAQIIndexSensor(MontrealAQIBaseSensor):
    """AQI numeric value sensor (0-500+)."""

    _attr_device_class = SensorDeviceClass.AQI
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_has_entity_name = True
    _attr_translation_key = "aqi"
    _attr_icon = "mdi:weather-hazy"

    def __init__(
        self,
        coordinator: MontrealAQICoordinator,
        device_info: DeviceInfo,
        entry_id: str,
        station_id: str,
    ) -> None:
        """Initialize AQI index sensor."""
        super().__init__(coordinator, device_info, entry_id, station_id)
        self._attr_unique_id = f"{DOMAIN}_{station_id}_aqi"

    @property
    def native_value(self) -> int | None:
        """Return AQI value."""
        value = self.coordinator.data.get("aqi")
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            _LOGGER.warning("Invalid AQI value for station %s: %s", self._station_id, value)
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes including measurement timestamp."""
        return {
            "measurement_timestamp": self.coordinator.data.get("timestamp"),
        }


# -------------------------------------------------------------------
# AQI level sensor (textual)
# -------------------------------------------------------------------


class MontrealAQILevelSensor(MontrealAQIBaseSensor):
    """AQI qualitative level sensor (Good/Acceptable/Bad)."""

    _attr_entity_registry_visible_default = False
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["good", "acceptable", "bad"]
    _attr_has_entity_name = True
    _attr_translation_key = "aqi_level"
    _attr_icon = "mdi:checkbox-marked-circle-outline"

    def __init__(
        self,
        coordinator: MontrealAQICoordinator,
        device_info: DeviceInfo,
        entry_id: str,
        station_id: str,
    ) -> None:
        """Initialize AQI level sensor."""
        super().__init__(coordinator, device_info, entry_id, station_id)
        self._attr_unique_id = f"{DOMAIN}_{station_id}_aqi_level"

    @property
    def native_value(self) -> str | None:
        """Return AQI level based on AQI value."""
        aqi = self.coordinator.data.get("aqi")
        if aqi is None:
            return None

        try:
            aqi_value = float(aqi)
        except (ValueError, TypeError):
            _LOGGER.warning(
                "Invalid AQI value for level calculation (station %s): %s",
                self._station_id,
                aqi,
            )
            return None

        if aqi_value <= 25:
            return "good"
        if aqi_value <= 50:
            return "acceptable"
        return "bad"

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        """Return dominant pollutant and measurement timestamp as attributes."""
        return {
            "dominant_pollutant": self.coordinator.data.get("dominant_pollutant"),
            "measurement_timestamp": self.coordinator.data.get("timestamp"),
        }


# -------------------------------------------------------------------
# Pollutant sensors
# -------------------------------------------------------------------


class MontrealAQIPollutantSensor(MontrealAQIBaseSensor):
    """Sensor for an individual pollutant concentration."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 0
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MontrealAQICoordinator,
        device_info: DeviceInfo,
        entry_id: str,
        station_id: str,
        code: str,
        meta: dict[str, Any],
    ) -> None:
        """Initialize pollutant sensor.

        Args:
            coordinator: Data coordinator
            device_info: Device information
            entry_id: Config entry ID
            station_id: Station ID
            code: Pollutant code (e.g., 'PM2.5')
            meta: Metadata for the pollutant from DEVICE_CLASS_MAP
        """
        super().__init__(coordinator, device_info, entry_id, station_id)
        self._code = code
        self._attr_translation_key = meta["key"]
        self._attr_native_unit_of_measurement = meta["unit"]
        self._attr_icon = meta["icon"]
        self._attr_device_class = meta.get("device_class")
        self._attr_unique_id = f"{DOMAIN}_{station_id}_{meta['key']}"

    @property
    def native_value(self) -> float | None:
        """Return pollutant concentration value."""
        pollutants = self.coordinator.data.get("pollutants", {})
        value = pollutants.get(self._code)

        if value is None:
            return None

        raw_value = value.get("concentration") if isinstance(value, dict) and "concentration" in value else value

        if raw_value is None:
            return None

        try:
            return float(raw_value)
        except (ValueError, TypeError):
            _LOGGER.warning(
                "Invalid pollutant value for %s (station %s): %s",
                self._code,
                self._station_id,
                value,
            )
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return measurement timestamp as attribute."""
        return {
            "measurement_timestamp": self.coordinator.data.get("timestamp"),
        }


# -------------------------------------------------------------------
# Timestamp sensor
# -------------------------------------------------------------------


class MontrealAQITimestampSensor(MontrealAQIBaseSensor):
    """Timestamp of the last AQI measurement."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_has_entity_name = True
    _attr_translation_key = "timestamp"

    def __init__(
        self,
        coordinator: MontrealAQICoordinator,
        device_info: DeviceInfo,
        entry_id: str,
        station_id: str,
    ) -> None:
        """Initialize timestamp sensor."""
        super().__init__(coordinator, device_info, entry_id, station_id)
        self._attr_unique_id = f"{DOMAIN}_{station_id}_timestamp"

    @property
    def native_value(self) -> datetime | None:
        """Return timestamp of last measurement."""
        ts = self.coordinator.data.get("timestamp")
        if ts is None:
            return None

        if isinstance(ts, datetime):
            return ts

        if isinstance(ts, str):
            try:
                parsed = dt_util.parse_datetime(ts)
                if parsed is None:
                    _LOGGER.warning(
                        "Failed to parse timestamp for station %s: %s",
                        self._station_id,
                        ts,
                    )
                return parsed
            except Exception as err:
                _LOGGER.warning(
                    "Error parsing timestamp for station %s: %s",
                    self._station_id,
                    err,
                )
                return None

        _LOGGER.warning(
            "Unexpected timestamp type for station %s: %s",
            self._station_id,
            type(ts),
        )
        return None
