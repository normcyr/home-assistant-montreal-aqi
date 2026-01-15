from unittest.mock import AsyncMock

from custom_components.montreal_aqi.const import DEVICE_CLASS_MAP
from custom_components.montreal_aqi.sensor import MontrealAQIPollutantSensor


async def test_pollutant_sensor_unique_id(device_info, mock_config_entry):
    coordinator = AsyncMock()
    coordinator.last_update_success = True
    coordinator.data = {"pollutants": {"NO2": {"concentration": 15}}}

    meta = {
        "key": "no2",
        "name": "NO2",
        "icon": "mdi:molecule",
        "unit": "µg/m³",
    }

    sensor = MontrealAQIPollutantSensor(
        coordinator=coordinator,
        station_id="80",
        code="NO2",
        meta=meta,
        device_info=device_info("80"),
        entry_id="",
    )

    assert sensor.native_value == 15
    assert sensor.unique_id.endswith("_no2")


async def test_pollutant_not_created_if_missing():
    data = {"pollutants": {"PM2.5": {"concentration": 10}}}

    created_codes = [code for code in DEVICE_CLASS_MAP if code in data["pollutants"]]

    assert "CO" not in created_codes
    assert "PM2.5" in created_codes
