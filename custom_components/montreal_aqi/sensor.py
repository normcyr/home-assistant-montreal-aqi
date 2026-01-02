from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import (
    DeviceInfo,
    EntityCategory,
    SensorDeviceClass,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (
    AQI_DESCRIPTION,
    AQI_LEVEL_DESCRIPTION,
    CONF_STATION_ID,
    DEVICE_CLASS_MAP,
    DOMAIN,
)
from .coordinator import MontrealAQICoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up Montreal AQI sensors from a config entry."""
    coordinator: MontrealAQICoordinator = hass.data[DOMAIN][entry.entry_id]

    sensors: list[SensorEntity] = [
        MontrealAQISensor(coordinator, entry, AQI_DESCRIPTION),
        MontrealAQISensor(coordinator, entry, AQI_LEVEL_DESCRIPTION),
        MontrealAQITimestampSensor(coordinator, entry),
    ]

    pollutants = coordinator.data.get("pollutants", {})

    for code, meta in DEVICE_CLASS_MAP.items():
        if code not in pollutants:
            continue

        sensors.append(
            MontrealAQIPollutantSensor(
                coordinator,
                entry,
                code,
                meta,
            )
        )

    async_add_entities(sensors, update_before_add=True)


class MontrealAQIBaseEntity(CoordinatorEntity, SensorEntity):
    """Base entity for all Montreal AQI sensors."""

    _attr_should_poll = False

    def __init__(
        self,
        coordinator: MontrealAQICoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self.station_id = entry.data[CONF_STATION_ID]

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.station_id)},
            name=f"Montreal AQI Station {self.station_id}",
            manufacturer="Ville de Montréal",
            model="Air Quality Monitoring Station",
        )


class MontrealAQISensor(MontrealAQIBaseEntity):
    """AQI and AQI level sensors."""

    def __init__(
        self,
        coordinator: MontrealAQICoordinator,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator, entry)
        self.entity_description = description

        station = entry.data[CONF_STATION_ID]
        self._attr_unique_id = f"{entry.entry_id}_station_{station}_{description.key}"
        self._attr_name = f"Station {station} {description.name}"

        if description is AQI_LEVEL_DESCRIPTION:
            self._attr_entity_registry_visible_default = False

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data

        if self.entity_description.key == "aqi":
            return data.get("aqi")

        if self.entity_description is AQI_LEVEL_DESCRIPTION:
            aqi = data.get("aqi")
            if aqi is None:
                return None
            if aqi <= 25:
                return "Good"
            if aqi <= 50:
                return "Acceptable"
            return "Bad"

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if self.entity_description is AQI_LEVEL_DESCRIPTION:
            return {"dominant_pollutant": self.coordinator.data.get("dominant_pollutant")}
        return {}


class MontrealAQIPollutantSensor(MontrealAQIBaseEntity):
    """Individual pollutant concentration sensor."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_suggested_display_precision = 1

    def __init__(
        self,
        coordinator: MontrealAQICoordinator,
        entry: ConfigEntry,
        code: str,
        meta: dict[str, Any],
    ) -> None:
        super().__init__(coordinator, entry)
        self.code = code

        self.entity_description = SensorEntityDescription(
            key=meta["key"],
            name=meta["name"],
            native_unit_of_measurement=meta["unit"],
            icon=meta["icon"],
        )

        station = entry.data[CONF_STATION_ID]
        self._attr_unique_id = f"{entry.entry_id}_station_{station}_{meta['key']}"
        self._attr_name = f"Station {station} {meta['name']}"

    @property
    def native_value(self) -> float | None:
        pollutant = self.coordinator.data.get("pollutants", {}).get(self.code)
        if not pollutant:
            return None

        value = pollutant.get("concentration")
        return float(value) if value is not None else None


class MontrealAQITimestampSensor(MontrealAQIBaseEntity):
    """Timestamp of the last AQI measurement."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
        self,
        coordinator: MontrealAQICoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)

        station = entry.data[CONF_STATION_ID]
        self._attr_unique_id = f"{entry.entry_id}_station_{station}_timestamp"
        self._attr_name = f"Station {station} Measurement Time"

    @property
    def native_value(self):
        ts = self.coordinator.data.get("timestamp")
        return dt_util.parse_datetime(ts) if ts else None
