"""Documentation for Load Pegelonline Timeseries

# Load Pegelonline Timeseries

## Description
Loads single timeseries from Pegelonline

Pegelonline (https://www.pegelonline.wsv.de/) provides German water level data via a website and an API.
This component allows to fetch a single such timeseries from the API.

## Inputs
* station (STRING): Either a station's UUID or its shortname
* timestampFrom (STRING): time interval start as isoformat timestamp string
* timestampTo (STRING): time interval end as isoformat timestamp string
* measurement (STRING): Either "W" for water level or "Q" for discharge

## Outputs
* timeseries (SERIES): The loaded timeseries. Station metadata is made available via the .attrs attribute.

## Details
* Currently Pegelonline provides data for the last 30 days. Historical data can be downloaded separately but cannot be accessed via the API and therefore not via this component.
* Identifying stations via its shortname required loading the full station list. Using UUID therefore

## Examples
E.g https://pegelonline.wsv.de/webservices/rest-api/v2/stations/593647aa-9fea-43ec-a7d6-6476a76ae868.json is a station that provides water level data which you can query either using the UUID or its shortname "BONN".
"""

from uuid import UUID

import pandas as pd
import requests

from hetdesrun.dt_utils import resolve_interval


def load_station_by_uuid(station_uuid: UUID) -> dict:
    """Loads station info from Pegelonline by uuid.

    May raise Errors from failed requests / json parsing.
    """
    url = f"https://pegelonline.wsv.de/webservices/rest-api/v2/stations/{str(station_uuid)}.json"
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    station = response.json()

    return station


def find_station_by_shortname(short_name: str) -> dict:
    """Loads single station info from Pegelonline by shortname.

    * case-insensitive
    * raises ValueError if station could not be found or not unique.
    * may raise Errors from failed requests / json parsing.
    """
    url = "https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations.json"
    response = requests.get(url, headers={"Accept-Encoding": "gzip"}, timeout=30)
    response.raise_for_status()

    stations = response.json()
    stations = [s for s in stations if s.get("shortname").lower() == short_name.lower()]

    if len(stations) != 1:
        raise ValueError(f"Could not find Pegelonline stations with shortname {short_name}")

    return stations[0]


def get_station(station: str) -> dict:
    """Obtain station from either short_name or uuid

    station: station shortname or uuid as string

    Note: Since pegelonline API has not single-station-by-shortname
    endpoint, if you provide a shortname, this needs to fetch the
    complete station list (2025-10-29: several hundred stations).
    """
    try:
        station_uuid = UUID(station)
    except (ValueError, TypeError):
        return find_station_by_shortname(station)
    else:
        return load_station_by_uuid(station_uuid)


def load_pegelonline_timeseries(
    station_uuid: UUID, timestamp_from: str, timestamp_to: str, measurement: str = "W"
) -> pd.Series:
    """
    Load single timeseries data from Pegelonline API.

    Args:
        station_uuid: Station UUID
        timestamp_from: Start timestamp (ISO format)
        timestamp_to: End timestamp (ISO format)
        measurement: 'W' for water level, 'Q' for discharge

    Returns:
        pd.Series with DatetimeIndex and values
    """

    url = f"https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations/{str(station_uuid)}/{measurement}/measurements.json"

    start, end = resolve_interval(timestamp_from, timestamp_to)

    params = {
        "start": start.isoformat(),
        "end": end.isoformat(),
    }

    response = requests.get(url, params=params, headers={"Accept-Encoding": "gzip"}, timeout=30)
    response.raise_for_status()

    data = pd.DataFrame(response.json())
    data["timestamp"] = pd.to_datetime(data["timestamp"])

    return pd.Series(
        data=data["value"].values,
        index=data["timestamp"],
        name=f"{str(station_uuid)}_{measurement}",
    ).sort_index()


# %%
# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "station": {"data_type": "STRING"},
        "timestampFrom": {"data_type": "STRING"},
        "timestampTo": {"data_type": "STRING"},
        "measurement": {"data_type": "STRING", "default_value": "W"},
    },
    "outputs": {
        "timeseries": {"data_type": "SERIES"},
    },
    "name": "Load Pegelonline Timeseries",
    "category": "Data Sources",
    "description": "Load single timeseries from Pegelonline",
    "version_tag": "0.1.0",
    "id": "230dfa9a-0efe-4418-a5b4-2ac3954ebd8f",
    "revision_group_id": "17eb8a67-fbce-452c-a1b7-2403a6834ce2",
    "state": "RELEASED",
    "released_timestamp": "2025-10-29T12:53:20.842136+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, station, timestampFrom, timestampTo, measurement="W"):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    station = get_station(station)
    timeseries = load_pegelonline_timeseries(
        station_uuid=station["uuid"],
        timestamp_from=timestampFrom,
        timestamp_to=timestampTo,
        measurement=measurement,
    )
    timeseries.name = station["shortname"] + "_" + station["uuid"]
    timeseries.attrs["station"] = station

    return {"timeseries": timeseries}


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "station",
            "filters": {"value": "593647aa-9fea-43ec-a7d6-6476a76ae868"},
        },
        {
            "workflow_input_name": "timestampFrom",
            "filters": {"value": "2025-10-15T00:00:00Z"},
        },
        {
            "workflow_input_name": "timestampTo",
            "filters": {"value": "2025-10-30T00:00:00Z"},
        },
        {
            "workflow_input_name": "measurement",
            "use_default_value": True,
            "filters": {"value": "W"},
        },
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "station",
            "filters": {"value": "593647aa-9fea-43ec-a7d6-6476a76ae868"},
        },
        {
            "workflow_input_name": "timestampFrom",
            "filters": {"value": "2025-10-15T00:00:00Z"},
        },
        {
            "workflow_input_name": "timestampTo",
            "filters": {"value": "2025-10-30T00:00:00Z"},
        },
        {
            "workflow_input_name": "measurement",
            "use_default_value": True,
            "filters": {"value": "W"},
        },
    ]
}


# %%
