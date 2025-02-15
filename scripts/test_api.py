import argparse
import logging

import requests

# API URL and Resource ID
API_URL = "https://donnees.montreal.ca/api/3/action/datastore_search"
RESOURCE_ID = "a25fdea2-7e86-42ac-8301-ca77db3ff17e"
STATION_ID = None  # Change to your desired station
LIST_RESOURCE_ID = "29db5545-89a4-4e4a-9e95-05aa6dc2fd80"


class Pollutant:
    def __init__(self, name: str, fullname: str, ref_value: int):
        self.name = name
        self.fullname = fullname
        self.ref_value = ref_value
        self.hour = 0
        self.value = 0
        self.aqi_value = 0

    def set_value(self, value: float):
        """
        Set the value (concentration) for the pollutant
        """
        self.value = float(value)

    def set_hour(self, hour: int):
        """
        Set the hour (time) at which the data was recorded
        """
        self.hour = int(hour)

    def aqi_contribution(self):
        """
        Calculate the AQI contribution of this pollutant using the formula:
        AQI = (value / ref_value) * 50
        """
        if self.value is not None and self.ref_value is not None:
            self.aqi_value = (self.value / self.ref_value) * 50
        else:
            raise ValueError(
                "Both value and ref_value must be set before calculating AQI."
            )

    def __repr__(self):
        return (
            f"Pollutant("
            f"name='{self.name}', "
            f"fullname='{self.fullname}', "
            f"ref_value={self.ref_value}, "
            f"value={self.value}, "
            f"aqi={self.aqi_value}, "
            f"hour={self.hour}"
            f")"
        )


# Creating pollutant instances
SO2 = Pollutant(name="SO2", fullname="sulfur dioxide", ref_value=500)
CO = Pollutant(name="CO", fullname="carbon monoxide", ref_value=35)
O3 = Pollutant(name="O3", fullname="ozone", ref_value=160)
NO2 = Pollutant(name="NO2", fullname="nitrogen dioxide", ref_value=400)
PM = Pollutant(name="PM", fullname="particulate matter, PM2.5", ref_value=35)


def get_latest_data(station_id):
    """
    Fetch the latest AQI data for all pollutants at a given station
    """
    params = {"resource_id": RESOURCE_ID, "limit": 1000}
    try:
        logging.info(f"Fetching latest data for station {station_id}...")
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return None

    if response.status_code == 200:
        data = response.json()
        records = data.get("result", {}).get("records", [])

        # Filter by stationId
        filtered_data = [r for r in records if r.get("stationId") == station_id]

        if not filtered_data:
            logging.warning(f"No data found for station {station_id}")
            return None

        # Find at what time the latest data point was recorded
        max_hour = None
        for entry in filtered_data:
            if max_hour is None or int(entry["heure"]) > max_hour:
                max_hour = int(entry["heure"])

        # Filter to keep only the latest data point
        latest_data = []
        for entry in filtered_data:
            if int(entry["heure"]) == max_hour:
                latest_data.append(entry)

        logging.info(f"Found latest data at hour {max_hour}.")
        logging.debug(latest_data)

        return latest_data

    else:
        logging.error(f"API Error: {response.status_code}")

        return None


def assign_aqi_contribution(latest_data):
    """
    Calculate AQI contributions for each pollutant and store the results
    """
    pollutants = {"SO2": SO2, "CO": CO, "O3": O3, "NO2": NO2, "PM": PM}

    for entry in latest_data:
        pollutant_name = entry["polluant"]
        value = entry["valeur"]
        hour = entry["heure"]

        # If the pollutant is not already in the list, create a new Pollutant object
        if pollutant_name not in pollutants:
            logging.info(f"Creating new Pollutant object for {pollutant_name}")
            pollutants[pollutant_name] = Pollutant(pollutant_name)

        # Set the value and hour for the corresponding pollutant
        pollutants[pollutant_name].set_value(value)
        pollutants[pollutant_name].set_hour(hour)

        # Calculate AQI for the pollutant and store the result in the object
        pollutants[pollutant_name].aqi_contribution()

    for pollutant in pollutants.values():
        logging.debug(f"{pollutant}")

    return pollutants


def sum_aqi_values(pollutants):
    """
    Sum up the AQI values of all pollutants in the collection
    """
    total_aqi = sum(pollutant.aqi_value for pollutant in pollutants.values())
    logging.debug(f"Total AQI value: {total_aqi}")
    return total_aqi


def get_list_stations():
    params = {"resource_id": LIST_RESOURCE_ID}
    try:
        logging.info("Fetching list of monitoring stations...")
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return None

    if response.status_code == 200:
        data = response.json()
        records = data.get("result", {}).get("records", [])
        list_stations = []
        for record in records:
            if record["statut"] == "ouvert":
                station_info = {
                    "station_id": record["numero_station"],
                    "station_name": record["nom"],
                    "station_address": record["adresse"],
                    "station borough": record["arrondissement_ville"],
                }
                logging.debug(station_info)
                list_stations.append(station_info)

        logging.info("Found a list of monitoring stations.")
        logging.info(list_stations)

        return list_stations

    else:
        logging.error(f"API Error: {response.status_code}")

        return None


if __name__ == "__main__":
    """
    Run the test
    """

    # Argument parser to handle CLI options
    parser = argparse.ArgumentParser(
        description="Fetch the air quality index from a monitoring station on the island of Montréal"
    )
    parser.add_argument("--debug", action="store_true", help="enable debug logging")
    parser.add_argument("--station", type=str, help="specify the station number")
    parser.add_argument(
        "--list",
        action="store_true",
        help="list the station numbers and their location",
    )
    args = parser.parse_args()

    # Configure logging
    if args.debug:
        LOGLEVEL = logging.DEBUG
    else:
        LOGLEVEL = logging.INFO

    logging.basicConfig(
        level=LOGLEVEL,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logging.debug("Debug mode enabled")

    # Get list of stations
    if args.list:
        list_stations = get_list_stations()
        exit()

    # Check whether a station ID was specified
    if args.station is None:
        STATION_ID = input("Enter Station ID: ").strip()
    else:
        STATION_ID = args.station

    # Get the latest data from specified station
    latest_data = get_latest_data(STATION_ID)
    if latest_data:
        pollutants = assign_aqi_contribution(latest_data)
        total_aqi = int(round(sum_aqi_values(pollutants), 0))
        logging.info(f"The air quality index for station {STATION_ID} is {total_aqi}.")
