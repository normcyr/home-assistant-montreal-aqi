"""Constants for Montreal AQI integration."""

from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import CONCENTRATION_MICROGRAMS_PER_CUBIC_METER

# Integration identifiers
DOMAIN = "montreal_aqi"
PLATFORMS = ["sensor"]

# Configuration keys
CONF_STATION_ID = "station_id"
CONF_STATION_NAME = "station_name"

# Update interval: 30 minutes (official API update frequency)
# For development/testing: timedelta(minutes=5)
UPDATE_INTERVAL = timedelta(minutes=30)

# -------------------------------------------------------------------
# Sensor Descriptions
# -------------------------------------------------------------------

AQI_DESCRIPTION = SensorEntityDescription(
    key="aqi",
    name="Air Quality Index",
    device_class=SensorDeviceClass.AQI,
    state_class=SensorStateClass.MEASUREMENT,
    icon="mdi:weather-hazy",
)
"""Sensor description for AQI numeric value (0-500+)."""

AQI_LEVEL_DESCRIPTION = SensorEntityDescription(
    key="aqi_level",
    name="Air Quality Level",
    device_class=SensorDeviceClass.ENUM,
    icon="mdi:checkbox-marked-circle-outline",
)
"""Sensor description for AQI qualitative level (Good/Acceptable/Bad).

Note: Options are set via _attr_options in MontrealAQILevelSensor, not here.
"""

# -------------------------------------------------------------------
# Pollutant Device Classes and Units
# -------------------------------------------------------------------

DEVICE_CLASS_MAP: dict[str, dict[str, Any]] = {
    # Mapping of pollutant codes to sensor metadata.
    # Each pollutant includes: key, name, device_class, unit, icon.
    "PM2.5": {
        "key": "pm25",
        "name": "PM2.5",
        "device_class": SensorDeviceClass.PM25,
        "unit": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        "icon": "mdi:blur",
    },
    "PM10": {
        "key": "pm10",
        "name": "PM10",
        "device_class": SensorDeviceClass.PM10,
        "unit": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        "icon": "mdi:dots-grid",
    },
    "NO2": {
        "key": "no2",
        "name": "NO₂",
        "device_class": SensorDeviceClass.NITROGEN_DIOXIDE,
        "unit": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        "icon": "mdi:chemical-weapon",
    },
    "O3": {
        "key": "o3",
        "name": "Ozone",
        "device_class": SensorDeviceClass.OZONE,
        "unit": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        "icon": "mdi:weather-hazy",
    },
    "SO2": {
        "key": "so2",
        "name": "SO₂",
        "device_class": SensorDeviceClass.SULPHUR_DIOXIDE,
        "unit": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        "icon": "mdi:smog",
    },
    "CO": {
        "key": "co",
        "name": "CO",
        "device_class": SensorDeviceClass.CO,
        "unit": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        "icon": "mdi:skull-crossbones",
    },
}

# -------------------------------------------------------------------
# Unit Conversions
# -------------------------------------------------------------------

PPB_TO_UGM3: dict[str, float] = {
    # Convert PPB (Parts Per Billion) to µg/m³ using MW/24.45.
    "O3": 48.00 / 24.45,
    "NO2": 46.01 / 24.45,
    "SO2": 64.07 / 24.45,
    "CO": 28.01 / 24.45,
}
