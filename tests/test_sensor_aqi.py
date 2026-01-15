from unittest.mock import AsyncMock

from custom_components.montreal_aqi.sensor import MontrealAQILevelSensor


def _make_coordinator(aqi):
    coordinator = AsyncMock()
    coordinator.last_update_success = True
    coordinator.data = {"aqi": aqi}
    return coordinator


def test_aqi_level_good(device_info):
    sensor = MontrealAQILevelSensor(
        coordinator=_make_coordinator(20),
        station_id="80",
        device_info=device_info("80"),
        entry_id="",
    )
    assert sensor.native_value == "Good"


def test_aqi_level_acceptable(device_info):
    sensor = MontrealAQILevelSensor(
        coordinator=_make_coordinator(40),
        station_id="80",
        device_info=device_info("80"),
        entry_id="",
    )
    assert sensor.native_value == "Acceptable"


def test_aqi_level_bad(device_info):
    sensor = MontrealAQILevelSensor(
        coordinator=_make_coordinator(80),
        station_id="80",
        device_info=device_info("80"),
        entry_id="",
    )
    assert sensor.native_value == "Bad"


def test_aqi_level_none(device_info):
    sensor = MontrealAQILevelSensor(
        coordinator=_make_coordinator(None),
        station_id="80",
        device_info=device_info("80"),
        entry_id="",
    )
    assert sensor.native_value is None
