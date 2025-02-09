# Air Quality Index (AQI) Integration for Home Assistant

![Icon for the integration](icon.png)

This project provides a Home Assistant integration to retrieve and display real-time Air Quality Index (AQI) data from a monitoring station on the island of Montréal from open data of the Réseau de surveillance de la qualité de l'air (RSQA) [API](https://donnees.montreal.ca/dataset/rsqa-indice-qualite-air/resource/a25fdea2-7e86-42ac-8301-ca77db3ff17e)). 

It calculates AQI values based on pollutants (SO2, CO, O3, NO2, PM) and exposes the results as a sensor with attributes for each pollutant level, including the station's timestamp.

List and location of the stations can be found [here](https://donnees.montreal.ca/dataset/rsqa-liste-des-stations/resource/29db5545-89a4-4e4a-9e95-05aa6dc2fd80).

## Features

- Fetch AQI data from a public API ([Montréal’s air quality dataset](https://donnees.montreal.ca/dataset/rsqa-indice-qualite-air/resource/a25fdea2-7e86-42ac-8301-ca77db3ff17e)).
- Display total AQI value and individual pollutant levels as attributes.
- Supports a configurable station ID via Home Assistant's user interface.

## Requirements

- Home Assistant instance.
- Internet connection to fetch real-time AQI data.

## Installation

### 1. Download the Repository

Clone this repository.

```bash
git clone https://github.com/yourusername/home-assistant-montreal-aqi.git
```

And copy the folder `custom_components/montreal_aqi` into the `custom_components` folder of your Home Assistant instance.

### 2. Configuration in Home Assistant

The integration can then be added directly via the Home Assistant UI:

- Go to Configuration > Integrations.
- Search for Montreal AQI and click on it.
- Follow the on-screen instructions to set up the integration by selecting the desired air quality monitoring station (available from the Montréal dataset).

### 3. Restart Home Assistant

To apply the changes, restart Home Assistant:

```bash
# In the Home Assistant UI:
Configuration > Server Controls > Restart
```

## Usage

After installation, the integration will create a sensor that reports:

- **State**: The overall AQI value.
- **Attributes**:
  - `SO2`: Sulfur dioxide concentration.
  - `CO`: Carbon monoxide concentration.
  - `O3`: Ozone concentration.
  - `NO2`: Nitrogen dioxide concentration.
  - `PM`: Particulate matter concentration.
  - `timestamp`: The measurement date as a timestamp.

You can use this sensor in your Home Assistant dashboard, for automation, or for logging purposes.

## Development

### Requirements

- Python 3.8+
- Home Assistant development environment

### Testing Locally

To test the integration locally:

1. Clone the repository to your local machine.
2. Install required dependencies:

```bash
pip install -r requirements.txt
```

3. Run the Python script test_api.py to simulate fetching AQI data and testing the calculations:

```bash
python test_api.py
```

### Contributing

We welcome contributions! To contribute:

1. Fork this repository.
2. Create a feature branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -am 'Add new feature'`).
4. Push to your branch (`git push origin feature-branch`).
5. Open a pull request.


## Technical Data

### Reference Values for Pollutants

The following table lists the reference values for each pollutant used in calculating the Air Quality Index (AQI) for the station data:

| Pollutant     | Full Name               | Reference Value |
|---------------|-------------------------|-----------------|
| SO₂           | Sulfur Dioxide          | 500 µg/m3       |
| CO            | Carbon Monoxide         | 35 mg/m3        |
| O₃            | Ozone                   | 160 µg/m3       |
| NO₂           | Nitrogen Dioxide        | 400 µg/m3       |
| PM (PM2.5)    | Particulate Matter      | 35 µg/m3        |

### AQI Calculation Method

The AQI for each pollutant is calculated using the following formula, as described [here](https://donnees.montreal.ca/dataset/rsqa-indice-qualite-air#methodology):

![AQI Equation](docs/aqi_equation.png)

where:
- `measured_value` is the concentration of the pollutant in µg/m³ measured at a given time.
- `reference_value` is the predefined reference value for the pollutant (as listed in the table above).
- `AQI` is the calculated air quality index value for that pollutant.

The AQI contribution for each pollutant is calculated individually using the formula, and the total AQI for the station is the sum of the individual pollutant AQIs. The total AQI provides an overall indication of air quality, helping to assess the overall health impact based on the measured pollutants.

The air quality index (AQI) value is defined as follows:

- Good: From 1 to 25
- Acceptable: From 26 to 50
- Poor: 51 or higher

## Licence

This project is licensed under the MIT Licence. See the [LICENCE](LICENCE) file for details.

## Disclaimer

I am not a formally trained programmer, and this project was developed as part of my learning journey. Throughout the process, I have received assistance from ChatGPT, which has helped me improve the code and understand various programming concepts. Any improvements or suggestions to make the code better are more than welcome! Contributions are encouraged and appreciated.
