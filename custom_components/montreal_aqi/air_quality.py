from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

# TODO: AirQualityEntity is deprecated, migrate to SensorEntity
from homeassistant.components.air_quality import AirQualityEntity
from homeassistant.const import CONCENTRATION_PARTS_PER_MILLION
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_STATION_ID, DOMAIN
from .coordinator import MontrealAQICoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Montreal AQI air quality entity from a config entry."""
    coordinator: MontrealAQICoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [MontrealAQIAirQualityEntity(coordinator, entry)],
        update_before_add=True,
    )


class MontrealAQIAirQualityEntity(
    CoordinatorEntity[MontrealAQICoordinator], AirQualityEntity
):
    """Aggregated Air Quality entity (qualitative)."""

    _attr_has_entity_name = True
    _attr_translation_key = "air_quality"

    def __init__(
        self,
        coordinator: MontrealAQICoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.entry = entry
        self.station_id = entry.data[CONF_STATION_ID]

        # 🔑 unicité par station
        self._attr_unique_id = f"{entry.entry_id}_station_{self.station_id}_air_quality"

        # use device portion + translation key for entity name
        self._attr_name = f"Station {self.station_id}"

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

    @property
    def state(self) -> str | None:
        """Return qualitative air quality level."""
        aqi = self.air_quality_index
        if aqi is None:
            return None

        if aqi <= 25:
            return "Good"
        if aqi <= 50:
            return "Acceptable"
        return "Bad"

    @property
    def unit_of_measurement(self) -> str:
        """Air quality entity has no unit."""
        return CONCENTRATION_PARTS_PER_MILLION

    @property
    def air_quality_index(self) -> int | None:
        value = self.coordinator.data.get("aqi")
        return int(value) if value is not None else None

    # --- Pollutants (optional but useful for dashboards) ---

    @property
    def particulate_matter_2_5(self) -> float | None:
        return self._pollutant("PM2.5")

    @property
    def particulate_matter_10(self) -> float | None:
        return self._pollutant("PM10")

    @property
    def nitrogen_dioxide(self) -> float | None:
        return self._pollutant("NO2")

    @property
    def ozone(self) -> float | None:
        return self._pollutant("O3")

    @property
    def sulphur_dioxide(self) -> float | None:
        return self._pollutant("SO2")

    @property
    def carbon_monoxide(self) -> float | None:
        return self._pollutant("CO")

    @property
    def extra_state_attributes(self) -> dict[str, str | int | None]:
        return {
            "air quality": self.state,
            "air quality index": self.air_quality_index,
            "dominant_pollutant": self.coordinator.data.get("dominant_pollutant"),
        }

    def _pollutant(self, code: str) -> float | None:
        pollutant = self.coordinator.data.get("pollutants", {}).get(code)
        if not pollutant:
            return None

        value = pollutant.get("concentration")
        return float(value) if value is not None else None
