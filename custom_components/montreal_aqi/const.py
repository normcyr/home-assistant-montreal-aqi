from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONCENTRATION_PARTS_PER_MILLION,
    CONCENTRATION_PARTS_PER_BILLION,
)

DOMAIN = "montreal_aqi"
CONF_STATION = "Montreal air quality monitoring station"
CONF_STATION_ID = "station_id"

POLLUTANTS = ["O3", "PM", "NO2", "SO2", "CO"]
REF_VALUES = {"SO2": 500, "CO": 35, "O3": 160, "NO2": 400, "PM": 35}
AQI_SENSOR = "AQI"


POLLUTANT_UNITS = {
    "O3": CONCENTRATION_PARTS_PER_BILLION,  # Ozone (O3) in ppb
    "PM": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,  # Particulate Matter (PM2.5/PM10) in µg/m³
    "NO2": CONCENTRATION_PARTS_PER_BILLION,  # Nitrogen Dioxide (NO2) in ppb
    "SO2": CONCENTRATION_PARTS_PER_BILLION,  # Sulfur Dioxide (SO2) in ppb
    "CO": CONCENTRATION_PARTS_PER_MILLION,  # Carbon Monoxide (CO) in ppm
}

API_URL = "https://donnees.montreal.ca/api/3/action/datastore_search"
RESOURCE_ID = "a25fdea2-7e86-42ac-8301-ca77db3ff17e"
LIST_RESOURCE_ID = "29db5545-89a4-4e4a-9e95-05aa6dc2fd80"
UPDATE_INTERVAL = 600
