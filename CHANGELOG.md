# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] - 2026-01-26

### Added
- **Multi-language support**: English, French, and Spanish translations
  - Localized config flow setup labels and error messages
  - Localized entity names for all sensor types
  - Translations managed via `strings.json` and translation files

### Changed
- **Improved entity IDs**: Station ID now included in AQI entity IDs to prevent conflicts between multiple stations
- **Timestamp precision**: Aligned timestamps with data collection time for better accuracy

### Fixed
- **Error handling**: Improved coordinator error handling for stations without available data
- **Data validation**: Strengthened pollutant raw value handling before float conversion
- **AsyncIO compatibility**: Fixed asyncio loop scope configuration to suppress deprecation warnings

### Technical
- Migrated to modern Home Assistant sensor entities
- Enabled time-series recording for all sensors
- Comprehensive test coverage for config flow and sensor operations

## [0.6.0] - Previous Release

- Initial stable release with core AQI monitoring functionality
