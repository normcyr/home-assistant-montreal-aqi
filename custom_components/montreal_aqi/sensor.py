from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (
    AQI_DESCRIPTION,
    AQI_LEVEL_DESCRIPTION,
    CONF_STATION_ID,
    DEVICE_CLASS_MAP,
    DOMAIN,
)

if TYPE_CHECKING:
    from datetime import datetime

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
    """Set up Montreal AQI sensors."""
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
        MontrealAQITimestampSensor(
            coordinator, device_info, entry.entry_id, station_id
        ),
    ]

    pollutants: dict[str, Any] = coordinator.data.get("pollutants", {})
    for code, meta in DEVICE_CLASS_MAP.items():
        if code not in pollutants:
            continue
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
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._entry_id = entry_id
        self._station_id = station_id

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success


# -------------------------------------------------------------------
# AQI index sensor
# -------------------------------------------------------------------


class MontrealAQIIndexSensor(MontrealAQIBaseSensor, SensorEntity):
    """AQI numeric value sensor."""

    entity_description = AQI_DESCRIPTION
    _attr_device_class = SensorDeviceClass.AQI
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: MontrealAQICoordinator,
        device_info: DeviceInfo,
        entry_id: str,
        station_id: str,
    ) -> None:
        super().__init__(coordinator, device_info, entry_id, station_id)
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{station_id}_aqi"

    @property
    def native_value(self) -> int | None:
        value = self.coordinator.data.get("aqi")
        return int(value) if value is not None else None


# -------------------------------------------------------------------
# AQI level sensor (textual)
# -------------------------------------------------------------------


class MontrealAQILevelSensor(MontrealAQIBaseSensor, SensorEntity):
    """AQI qualitative level sensor."""

    entity_description = AQI_LEVEL_DESCRIPTION
    _attr_entity_registry_visible_default = False
    _attr_icon = "mdi:signal"

    def __init__(
        self,
        coordinator: MontrealAQICoordinator,
        device_info: DeviceInfo,
        entry_id: str,
        station_id: str,
    ) -> None:
        super().__init__(coordinator, device_info, entry_id, station_id)
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{station_id}_aqi_level"

    @property
    def native_value(self) -> str | None:
        aqi = self.coordinator.data.get("aqi")
        if aqi is None:
            return None
        if aqi <= 25:
            return "Good"
        if aqi <= 50:
            return "Acceptable"
        return "Bad"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"dominant_pollutant": self.coordinator.data.get("dominant_pollutant")}


# -------------------------------------------------------------------
# Pollutant sensors
# -------------------------------------------------------------------


class MontrealAQIPollutantSensor(MontrealAQIBaseSensor, SensorEntity):
    """Sensor for an individual pollutant concentration."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(
        self,
        coordinator: MontrealAQICoordinator,
        device_info: DeviceInfo,
        entry_id: str,
        station_id: str,
        code: str,
        meta: dict[str, Any],
    ) -> None:
        super().__init__(coordinator, device_info, entry_id, station_id)
        self._code = code
        self.entity_description = SensorEntityDescription(
            key=f"{station_id}_{meta['key']}",
            name=f"Station {station_id} {meta['name']}",
            native_unit_of_measurement=meta["unit"],
            icon=meta["icon"],
            device_class=meta.get("device_class"),
        )
        self._attr_unique_id = f"{DOMAIN}_{station_id}_{meta['key']}"

    @property
    def native_value(self) -> float | None:
        pollutant = self.coordinator.data.get("pollutants", {}).get(self._code)
        if pollutant is None:
            return None
        value = pollutant.get("concentration")
        return float(value) if value is not None else None


# -------------------------------------------------------------------
# Timestamp sensor
# -------------------------------------------------------------------


class MontrealAQITimestampSensor(MontrealAQIBaseSensor, SensorEntity):
    """Timestamp of the last AQI measurement."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
        self,
        coordinator: MontrealAQICoordinator,
        device_info: DeviceInfo,
        entry_id: str,
        station_id: str,
    ) -> None:
        super().__init__(coordinator, device_info, entry_id, station_id)
        self._attr_unique_id = f"{entry_id}_{station_id}_timestamp"
        self._attr_name = f"Station {station_id} Measurement Time"

    @property
    def native_value(self) -> datetime | None:
        ts = self.coordinator.data.get("timestamp")
        return dt_util.parse_datetime(ts) if ts else None
