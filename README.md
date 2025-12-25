# Montreal Air Quality Index (AQI)

![Logo of the project](docs/montreal_aqi_logo.png)

A Home Assistant custom integration that exposes **air quality data for the City of Montréal (Québec, Canada)** using official open data.

This integration provides a qualitative **Air Quality** entity, numeric **AQI**, and detailed **pollutant sensors**, powered by the `montreal-aqi-api` Python library (more information about this library [here](https://github.com/normcyr/montreal-aqi-api)).

---

## ✨ Features

- Official Montréal RSQA AQI data
- Config flow (UI-based setup)
- Aggregated Air Quality entity
- Numeric AQI sensor
- Pollutant-level sensors (PM2.5, O₃, NO₂, SO₂, CO)
- Robust coordinator-based architecture
- Designed for dashboards and automations

---

## 📦 Installation

### Option 1 — HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Normcyr&repository=home-assistant-montreal-aqi&category=integration)

1. Open **HACS** in Home Assistant
2. Go to **Integrations**
3. Search for **Montreal Air Quality Index**
4. Install
5. Restart Home Assistant

### Option 2 — Manual

1. Download or clone this repository
2. Copy `custom_components/montreal_aqi` into:

   ```bash
   config/custom_components/
   ```

3. Restart Home Assistant

---

## ⚙️ Configuration

1. Go to **Settings → Devices & Services**
2. Click **Add Integration**
3. Search for **Montreal Air Quality Index**
4. Pick your air quality monitoring station
5. Confirm

The integration will start polling automatically.

---

## 📊 Entities Created

| Entity Type | Description |
|-------------|-------------|
| Air Quality | Qualitative AQI state (Good / Acceptable / Bad) |
| Sensor | Numeric AQI |
| Sensors | Individual pollutant concentrations |
| Sensor | Dominant pollutant |

All entities are grouped under a single device per station.

---

## 🧠 AQI Interpretation

| AQI Range | Meaning |
|-----------|---------|
| 0–25 | Good |
| 26–50 | Acceptable |
| 51+ | Bad |

---

## Home Assistant dashboard Examples

You can use these sensors in your dashboard with different Lovelace cards. 

*WIP*

---

## 🐞 Issues & Support

- Bug reports: https://github.com/normcyr/home-assistant-montreal-aqi/issues
- Feature requests welcome

---

## 📜 License

This project is licensed under the MIT Licence. See the [LICENSE](LICENSE) file for details.

## Disclaimer

I am not a formally trained programmer, and this project was developed as part of my learning journey. Throughout the process, I have received assistance from ChatGPT, which has helped me improve the code and understand various programming concepts. Any improvements or suggestions to make the code better are more than welcome! Contributions are encouraged and appreciated.
