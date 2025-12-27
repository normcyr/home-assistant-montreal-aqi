from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import CONCENTRATION_MICROGRAMS_PER_CUBIC_METER

DOMAIN = "montreal_aqi"
PLATFORMS = ["air_quality", "sensor"]

CONF_STATION_ID = "station_id"
CONF_STATION_NAME = "station_name"

UPDATE_INTERVAL = timedelta(minutes=30)  # production
# UPDATE_INTERVAL = timedelta(minutes=5)  # development/testing

AQI_DESCRIPTION = SensorEntityDescription(
    key="aqi",
    name="Air Quality Index",
    device_class=SensorDeviceClass.AQI,
    state_class=SensorStateClass.MEASUREMENT,
    icon="mdi:weather-hazy",
)
AQI_LEVEL_DESCRIPTION = SensorEntityDescription(
    key="iqa_level",
    name="Air Quality",
    device_class=SensorDeviceClass.ENUM,
    options=["Good", "Acceptable", "Bad"],
    icon="mdi:checkbox-marked-circle-outline",
)

DEVICE_CLASS_MAP: dict[str, dict[str, Any]] = {
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

PPB_TO_UGM3 = {
    "O3": 48.00 / 24.45,
    "NO2": 46.01 / 24.45,
    "SO2": 64.07 / 24.45,
    "CO": 28.01 / 24.45,
}
