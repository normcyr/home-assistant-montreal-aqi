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
