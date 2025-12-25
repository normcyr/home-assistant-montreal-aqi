# Montreal AQI — Documentation

This document provides **technical and advanced usage documentation** for the Montreal AQI Home Assistant integration.

---

## 📡 Data Source

Data is fetched from the **Ville de Montréal Open Data Portal**, specifically the RSQA (Réseau de surveillance de la qualité de l’air) dataset.

Methodology reference:
https://donnees.montreal.ca/dataset/rsqa-indice-qualite-air

---

## 🏗 Architecture

The integration uses the **Home Assistant DataUpdateCoordinator** pattern:

- One coordinator per station
- Centralized API polling
- All entities subscribe to coordinator updates
- Graceful handling of API failures

---

## 🧩 Platforms

- `air_quality`
- `sensor`

---

## 🧪 Pollutants Exposed

| Code | Name |
|-----|------|
| PM2.5 | Fine particulate matter |
| PM10 | Coarse particulate matter |
| O₃ | Ozone |
| NO₂ | Nitrogen dioxide |
| SO₂ | Sulfur dioxide |
| CO | Carbon monoxide |

Concentrations are estimated from AQI contribution values and should be treated as approximations.

---

## Home Assistant dashboard Examples

You can use these sensors in your dashboard with different Lovelace cards.
Replace `station_80` with the station number you want to monitor.

### History graph

```yaml
type: history-graph
title: Air Quality Index - Montréal, QC
hours_to_show: 48
refresh_interval: 300
entities:
  - entity: sensor.station_80_air_quality_index
    name: AQI
```

### Overlay history graph of several pollutants

```yaml
type: history-graph
title: Air Poluttants Levels - Montréal, QC
hours_to_show: 48
refresh_interval: 300
entities:
  - entity: sensor.station_80_so2
    name: SO2
  - entity: sensor.station_80_pm2_5
    name: PM2.5
  - entity: sensor.station_80_ozone
    name: O3
  - entity: sensor.station_80_no2
    name: NO2
```

### Vertical stack with information from each pollutant

```yaml
type: vertical-stack
cards:
  - type: tile
    entity: air_quality.montreal_aqi_station_3_station_3_air_quality
    name: Air Quality
    icon: mdi:weather-hazy
    color: accent
    vertical: false
    features_position: bottom
  - type: tile
    entity: sensor.station_3_air_quality_index
    name: Air Quality Index
    icon: mdi:gauge
  - type: entities
    title: Polluants (concentration)
    show_header_toggle: false
    entities:
      - entity: sensor.station_80_pm2_5
      - entity: sensor.station_80_no2
      - entity: sensor.station_80_ozone
      - entity: sensor.station_80_so2
```

---

## 🧠 Coordinator Update Logic

- Polling interval: defined in coordinator
- Uses `montreal-aqi-api` PyPI package
- API errors are logged and reflected in entity availability

---

## 🧪 Testing

The integration includes:

- Coordinator tests
- Platform setup tests
- Entity behavior tests
- Reload / unload tests

Run locally:

```bash
uv sync
uv run pytest
```

---

## 🧯 Troubleshooting

### Entities unavailable

- Check station ID validity
- Verify Montréal open data availability
- Enable debug logging:

```yaml
logger:
  default: info
  logs:
    custom_components.montreal_aqi: debug
```

---

## 🔁 Versioning & Compatibility

- Follows semantic versioning
- Requires Home Assistant 2025.5.0 or newer
- Backward compatibility maintained within minor versions

---

## 🧑‍💻 Development Notes

- Async-first implementation
- No blocking I/O
- Strict typing and linting
- Designed for HACS inclusion

---

## 📜 License

This project is licensed under the MIT Licence. See the [LICENSE](LICENSE) file for details.
