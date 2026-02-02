# Montreal AQI Home Assistant Integration - AI Coding Agent Guide

## Project Overview

This is a **Home Assistant custom component** for monitoring air quality data from the City of Montreal's official monitoring stations. It provides real-time AQI (Air Quality Index) values, qualitative air quality levels, and detailed pollutant concentration sensors using the official Montreal open data API.

**Tech Stack**: Python 3.12+, Home Assistant 2024.12.0+, async/await, `montreal-aqi-api` library

## Architecture

### Core Components

1. **`coordinator.py`** - `MontrealAQICoordinator`: Central data fetcher using HA's `DataUpdateCoordinator`
   - Fetches data from Montreal's RSQA (Réseau de surveillance de la qualité de l'air) API
   - Updates every 30 minutes (configurable via `UPDATE_INTERVAL` in `const.py`)
   - Handles API errors gracefully with `UpdateFailed` exceptions
   - Returns structured data: `aqi`, `dominant_pollutant`, `pollutants` dict, and `timestamp`

2. **`api.py`** - `MontrealAQIApi`: Async wrapper for the `montreal-aqi-api` library
   - Provides async methods: `async_list_stations()` and `async_get_station()`
   - Uses `hass.async_add_executor_job()` to run synchronous API calls in thread pool
   - Handles station listing for config flow and data fetching for coordinator

3. **`config_flow.py`** - `MontrealAQIConfigFlow`: Multi-step config flow for station selection
   - Single step: Lists available monitoring stations and lets user select one
   - Fetches station list from API during setup
   - Creates config entry with `station_id`

4. **`sensor.py`** - Entity implementations
   - **AQI Index Sensor**: Numeric AQI value (0-100+)
   - **AQI Level Sensor**: Qualitative level ("Good", "Acceptable", "Bad") with dominant pollutant attribute
   - **Pollutant Sensors**: Individual sensors for PM2.5, PM10, NO₂, O₃, SO₂, CO concentrations
   - **Timestamp Sensor**: Last measurement timestamp
   - All sensors inherit from `CoordinatorEntity` and share device info

5. **`const.py`** - Single source of truth for constants and sensor definitions
   - Sensor entity descriptions (`AQI_DESCRIPTION`, `AQI_LEVEL_DESCRIPTION`)
   - Pollutant mappings (`DEVICE_CLASS_MAP`) with device classes, units, icons
   - Update interval and configuration keys
   - Unit conversions (PPB to µg/m³)

### Data Flow

1. **Config Flow**: User selects station → Config entry created with `station_id`
2. **Setup**: Coordinator created with API instance → First data fetch
3. **Polling**: Every 30 minutes, coordinator calls `api.async_get_station(station_id)`
4. **Data Processing**: API returns dict with AQI, pollutants, timestamp
5. **Entity Updates**: All sensors update from coordinator data

### Sensor Types

| Sensor Type | Description | Device Class |
|-------------|-------------|--------------|
| AQI Index | Numeric AQI value | `SensorDeviceClass.AQI` |
| AQI Level | Qualitative level (Good/Acceptable/Bad) | `SensorDeviceClass.ENUM` |
| Pollutants | Individual pollutant concentrations | Varies (PM25, PM10, NO2, etc.) |
| Timestamp | Last measurement time | `SensorDeviceClass.TIMESTAMP` |

**Pollutant Sensors**: Only created for pollutants present in API response. Concentrations are in µg/m³.

## Setup (use devcontainer for consistency)

This project uses standard Python packaging with pip and modern tools for performance.

```bash
# Install dependencies with uv (faster than pip)
uv pip install -r requirements.txt
uv pip install -r requirements_dev.txt

# For testing
uv pip install -r requirements_test.txt
```

```bash
# Linting and formatting
ruff check custom_components/
ruff format custom_components/

# Type checking
mypy custom_components/montreal_aqi/

# Testing
pytest -v

# Coverage
pytest --cov=custom_components.montreal_aqi --cov-report=html

# Pre-commit hooks with prek (faster than pre-commit)
prek install
prek run --all-files
```

### Key Files to Check First

- `README.md`: User-facing features, installation, entity descriptions
- `DOCUMENTATION.md`: Technical details, data source, dashboard examples
- `pyproject.toml`: Python version, pytest/ruff/mypy config
- `requirements.txt*`: Dependencies for runtime, dev, and testing
- `custom_components/montreal_aqi/const.py`: Sensor definitions and constants
- `tests/conftest.py`: Test fixtures and mocks

## Dependency Management

### Key Dependencies

- `montreal-aqi-api==0.5.0` - Official Montreal AQI API wrapper (pinned in `manifest.json`)
- `homeassistant>=2024.12.0` - For development and testing
- `pytest-homeassistant-custom-component` - HA-specific testing utilities

### Updating Dependencies

- Update version in `manifest.json` and `requirements.txt`
- Test compatibility with HA version matrix
- Check API changes in `montreal-aqi-api` library

## Code Conventions

### Type Hints & Style

- Strict `mypy`: All functions need type hints
- Imports: Standard library → Third-party → HA → Local
- Line length: 88 chars (ruff default)
- Logging: Use `_LOGGER.debug/info/warning/error` with context

### Home Assistant Patterns

- Async first: Use `async def` for I/O operations
- Coordinator pattern: Entities read from `self.coordinator.data`
- Entity naming: `{station_id}_{sensor_type}` (e.g., `80_aqi`, `80_pm25`)
- Device registry: One device per station (all sensors grouped under it)
- Config flow: UI-based setup with station selection

### Sensor Availability & Attributes

Sensors are always available - they show last known values even during API outages.

**AQI Level Sensor Attributes:**
- `dominant_pollutant`: Code of the main pollutant affecting AQI

**All sensors include:**
- Device info linking to Montreal station
- Unique IDs based on station and sensor type

### AQI Interpretation

| AQI Range | Level | Meaning |
|-----------|-------|---------|
| 0–25 | Good | Air quality is satisfactory |
| 26–50 | Acceptable | Air quality is acceptable |
| 51+ | Bad | Air quality is poor |

## Testing Strategy

### Test Suite Requirements

Tests use `pytest` with HA custom component fixtures.

### Test Structure

**Key Test Fixtures (in `conftest.py`):**
- `mock_config_entry`: MockConfigEntry for station 80
- `mock_station_data`: Sample API response with AQI, pollutants
- `mock_api`: AsyncMock for API calls
- `device_info`: Factory for DeviceInfo objects

### Test Coverage Focus

- API error handling and `UpdateFailed` exceptions
- Sensor value extraction from coordinator data
- Pollutant sensor creation based on available data
- Timestamp parsing and device info

### Common Gotchas

- **API Response Format**: Montreal API returns data as dict with `aqi`, `pollutants` dict, `dominant_pollutant`, `timestamp`
- **Pollutant Availability**: Not all stations measure all pollutants - sensors only created for available pollutants
- **Concentration Units**: All concentrations in µg/m³, converted from API values as needed
- **Timestamp Handling**: API timestamps parsed with `dt_util.parse_datetime()`
- **Station IDs**: Numeric IDs (e.g., `80`) used as strings in some places, ints in others
- **Device Naming**: Uses "Montreal AQI Station {id}" format
- **Entity Registry**: AQI level sensor hidden by default (`_attr_entity_registry_visible_default = False`)

## Adding New Features

### Adding a New Sensor

1. Add entity description to `const.py` if needed
2. Create new sensor class in `sensor.py` inheriting from `MontrealAQIBaseSensor`
3. Add to sensor list in `async_setup_entry()`
4. Add tests in appropriate test file
5. Update translations if needed

### Adding New Pollutants

1. Add entry to `DEVICE_CLASS_MAP` in `const.py` with device class, unit, icon
2. Sensor creation is automatic if pollutant present in API response
3. Add test data to fixtures

### Modifying Update Interval

1. Change `UPDATE_INTERVAL` in `const.py`
2. Update tests that rely on timing

## External Dependencies

### montreal-aqi-api

- Available on PyPI
- Synchronous library wrapped with async executor jobs
- Provides `list_open_stations()` and `get_station_aqi(station_id)`
- Returns `Station` objects with `to_dict()` method
- **Important**: API calls are synchronous and wrapped with `hass.async_add_executor_job()` for async compatibility.

## Release Process

### Version Management

- **Current Version**: 0.6.0 (stable release)
- **Version Format**: Standard semantic versioning (X.Y.Z)

### Files to Update for Release

- `custom_components/montreal_aqi/manifest.json` - `version` field
- `pyproject.toml` - `version` field
- Create GitHub release with changelog

### Release Checklist

1. Update version numbers in `manifest.json` and `pyproject.toml`
2. Update `CHANGELOG.md` with new features/fixes
3. Commit and push changes
4. Create GitHub release with version tag
5. HACS will detect new version automatically

### Testing Before Release

- Run full test suite: `pytest`
- Check linting: `ruff check`
- Type check: `mypy`
- Manual testing in HA dev environment

## Commit & PR Guidelines

### Commit Message Format

Use conventional commits: `type(scope): description`

Examples:
- `feat: add new sensor`
- `fix(coordinator): resolve API error`
- `docs: update README`

### PR Requirements

- All tests pass
- Code linted and formatted
- Type hints complete
- Manual testing performed
- Update `README`/`DOCUMENTATION` if needed

## AI Agent Instructions

When working with this codebase:

- **Understand the simplicity**: This is a straightforward integration - coordinator fetches data, sensors display it
- **Check API responses**: Always verify what the `montreal-aqi-api` returns
- **Test with real stations**: Use station IDs like `80`, `39`, etc. for testing
- **Pollutant variations**: Different stations may have different pollutant sets
- **HA compatibility**: Ensure compatibility with HA 2024.12.0+ patterns
- **Critical**: The integration relies on the `montreal-aqi-api` library - any API changes require library updates. Always check the library's documentation and source code when debugging data issues.
