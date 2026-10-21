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
* timeseries (SERIES): The loaded timeseries with a UTC datetime index. Its metadata in the .attrs attribute follows the metadata conventions, see "Metadata" below.

## Details
* Currently Pegelonline provides data for the last 30 days. Historical data can be downloaded separately but cannot be accessed via the API and therefore not via this component.
* Identifying stations via its shortname required loading the full station list. Using UUID therefore
* Pegelonline provides timestamps in German local time (CET / CEST). They are converted to UTC.

### Metadata
The metadata of the timeseries follows the hetida designer [metadata conventions](https://hetida.github.io/hetida-designer/user_guide/attached_metadata/) for a SERIES:
* `dataset_metadata` contains the queried interval, as `ref_data_frequency` the interval in which Pegelonline provides values for the timeseries (e.g. "15min") and as `query_timestamp` the time of the request, since Pegelonline delivers its current state of the data.
* The single entry under `metrics` describes the timeseries: Its `id` is the station uuid and the measurement, e.g. "593647aa-9fea-43ec-a7d6-6476a76ae868_W". Its `name` consists of the names of station and timeseries, e.g. "BONN WASSERSTAND ROHDATEN". The value dimension "value" provides unit (e.g. "cm") and measurement ("water level" for "W", "discharge" for "Q"), and for water levels its description mentions the gauge zero. Its `path` consists of the water and the station, e.g. ["RHEIN", "BONN"], its `origin` is "Pegelonline", and it is recorded `periodic` with the interval of the values as `data_frequency`. The information on the station (uuid, number, names, water, km, agency, latitude and longitude) is available under `inherited`, e.g. "latitude" or "station_shortname".

This requires an additional request for the information on the timeseries (unit, interval, gauge zero).

## Examples
E.g https://pegelonline.wsv.de/webservices/rest-api/v2/stations/593647aa-9fea-43ec-a7d6-6476a76ae868.json is a station that provides water level data which you can query either using the UUID or its shortname "BONN".
"""

from datetime import UTC, datetime
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
    except ValueError, TypeError:
        return find_station_by_shortname(station)
    else:
        return load_station_by_uuid(station_uuid)


def load_timeseries_info(station_uuid: UUID, measurement: str) -> dict:
    """Loads the information on a timeseries of a station from Pegelonline, e.g. its unit

    May raise Errors from failed requests / json parsing.
    """
    url = f"https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations/{str(station_uuid)}/{measurement}.json"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def load_pegelonline_timeseries(
    station_uuid: UUID, start: datetime, end: datetime, measurement: str = "W"
) -> pd.Series:
    """
    Load single timeseries data from Pegelonline API.

    Args:
        station_uuid: Station UUID
        start: Start of the interval to load
        end: End of the interval to load
        measurement: 'W' for water level, 'Q' for discharge

    Returns:
        pd.Series with UTC DatetimeIndex and values
    """

    url = f"https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations/{str(station_uuid)}/{measurement}/measurements.json"

    params = {
        "start": start.isoformat(),
        "end": end.isoformat(),
    }

    response = requests.get(url, params=params, headers={"Accept-Encoding": "gzip"}, timeout=30)
    response.raise_for_status()

    data = pd.DataFrame(response.json(), columns=["timestamp", "value"])
    # Timestamps have offsets of German local time, which differ before and
    # after daylight saving time changes. utc=True converts them to UTC.
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True)

    return pd.Series(
        data=data["value"].values,
        index=data["timestamp"],
        name=f"{str(station_uuid)}_{measurement}",
    ).sort_index()


MEASUREMENTS = {"W": "water level", "Q": "discharge"}


def timeseries_metadata(
    station: dict,
    timeseries_info: dict,
    measurement: str,
    start: datetime,
    end: datetime,
    query_timestamp: datetime,
) -> dict:
    """Metadata of a loaded timeseries following the hetida designer metadata conventions"""
    metric_id = f"{station['uuid']}_{measurement}"
    timeseries_name = timeseries_info.get("longname") or measurement
    water = station.get("water") or {}
    equidistance = timeseries_info.get("equidistance")
    gauge_zero = timeseries_info.get("gaugeZero") or {}

    value_dimension = {
        "column": "value",
        "unit": timeseries_info.get("unit"),
        "measurement": MEASUREMENTS.get(measurement, timeseries_name),
        "value_data_type": "float",
    }
    frequency = f"{equidistance}min" if isinstance(equidistance, int) and equidistance > 0 else None
    if gauge_zero.get("value") is not None:
        value_dimension["description"] = (
            f"Relative to the gauge zero of {gauge_zero['value']} {gauge_zero.get('unit', '')}"
        ).rstrip()

    return {
        "dataset_metadata": {
            "metric_key": "id",
            "single_metric": metric_id,
            "queried_metrics": [metric_id],
            "ref_interval_start_timestamp": start.isoformat(),
            "ref_interval_end_timestamp": end.isoformat(),
            "ref_interval_type": "closed",
            **({"ref_data_frequency": frequency} if frequency is not None else {}),
            "query_timestamp": query_timestamp.isoformat(),
        },
        "metrics": [
            {
                "id": metric_id,
                "name": f"{station['longname']} {timeseries_name}",
                "description": f"{timeseries_name} of Pegelonline station {station['longname']}"
                + (f" on {water['longname']}" if water.get("longname") else ""),
                "value_dimensions": [value_dimension],
                "default_aggregation_method": "MEAN",
                "path": [
                    name
                    for name in (water.get("longname"), station["longname"])
                    if name is not None
                ],
                "origin": "Pegelonline",
                **(
                    {"recording_mode": "periodic", "data_frequency": frequency}
                    if frequency is not None
                    else {}
                ),
                "inherited": {
                    "station_uuid": station["uuid"],
                    "station_number": station.get("number"),
                    "station_shortname": station.get("shortname"),
                    "station_longname": station.get("longname"),
                    "water_shortname": water.get("shortname"),
                    "water_longname": water.get("longname"),
                    "km": station.get("km"),
                    "agency": station.get("agency"),
                    "latitude": station.get("latitude"),
                    "longitude": station.get("longitude"),
                },
            }
        ],
    }


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
    start, end = resolve_interval(timestampFrom, timestampTo)
    query_timestamp = datetime.now(tz=UTC)
    timeseries = load_pegelonline_timeseries(
        station_uuid=station["uuid"],
        start=start,
        end=end,
        measurement=measurement,
    )
    timeseries.name = station["shortname"] + "_" + station["uuid"]
    timeseries.attrs = timeseries_metadata(
        station,
        load_timeseries_info(station["uuid"], measurement),
        measurement,
        start,
        end,
        query_timestamp,
    )

    return {"timeseries": timeseries}


# Testing
try:
    import pytest
except ImportError:
    pass
else:
    from hetdesrun.models.metadata_conventions import check_metadata_conventions

    BONN = {
        "uuid": "593647aa-9fea-43ec-a7d6-6476a76ae868",
        "number": "2710080",
        "shortname": "BONN",
        "longname": "BONN",
        "km": 654.8,
        "agency": "STANDORT KÖLN",
        "longitude": 7.108045,
        "latitude": 50.736398,
        "water": {"shortname": "RHEIN", "longname": "RHEIN"},
    }
    # as provided by Pegelonline
    PEGELONLINE_RESPONSES = {
        "stations.json": [BONN],
        f"stations/{BONN['uuid']}.json": BONN,
        f"stations/{BONN['uuid']}/W.json": {
            "shortname": "W",
            "longname": "WASSERSTAND ROHDATEN",
            "unit": "cm",
            "equidistance": 15,
            "gaugeZero": {"unit": "m. ü. NHN", "value": 42.713, "validFrom": "2019-11-01"},
        },
        f"stations/{BONN['uuid']}/Q.json": {
            "shortname": "Q",
            "longname": "ABFLUSS_ROHDATEN",
            "unit": "m³/s",
            "equidistance": 15,
        },
        f"stations/{BONN['uuid']}/W/measurements.json": [
            {"timestamp": "2026-03-29T01:45:00+01:00", "value": 290.0},
            {"timestamp": "2026-03-29T03:00:00+02:00", "value": 291.0},
        ],
        f"stations/{BONN['uuid']}/Q/measurements.json": [
            {"timestamp": "2026-03-29T01:45:00+01:00", "value": 2010.0},
        ],
    }

    class FakeResponse:
        def __init__(self, url):
            self.content = PEGELONLINE_RESPONSES[url.split("/rest-api/v2/")[1]]

        def raise_for_status(self):
            pass

        def json(self):
            return self.content

    @pytest.fixture
    def pegelonline(monkeypatch):
        monkeypatch.setattr(requests, "get", lambda url, **_kwargs: FakeResponse(url))

    @pytest.mark.usefixtures("pegelonline")
    @pytest.mark.parametrize("station", ["BONN", BONN["uuid"]])
    def test_metadata_follows_conventions(station):
        timeseries = main(
            station=station,
            timestampFrom="2026-03-29T00:00:00+00:00",
            timestampTo="2026-03-29T02:00:00+00:00",
        )["timeseries"]

        assert list(timeseries) == [290.0, 291.0]  # noqa: S101
        assert check_metadata_conventions(timeseries) == []  # noqa: S101
        # the time of the request
        query_timestamp = timeseries.attrs["dataset_metadata"].pop("query_timestamp")
        assert abs(pd.Timestamp.now(tz="UTC") - pd.Timestamp(query_timestamp)) < pd.Timedelta(  # noqa: S101
            "1min"
        )
        assert timeseries.attrs["dataset_metadata"] == {  # noqa: S101
            "metric_key": "id",
            "single_metric": f"{BONN['uuid']}_W",
            "queried_metrics": [f"{BONN['uuid']}_W"],
            "ref_interval_start_timestamp": "2026-03-29T00:00:00+00:00",
            "ref_interval_end_timestamp": "2026-03-29T02:00:00+00:00",
            "ref_interval_type": "closed",
            "ref_data_frequency": "15min",
        }
        metric = timeseries.attrs["metrics"][0]
        assert metric["name"] == "BONN WASSERSTAND ROHDATEN"  # noqa: S101
        assert metric["path"] == ["RHEIN", "BONN"]  # noqa: S101
        assert metric["origin"] == "Pegelonline"  # noqa: S101
        assert (metric["recording_mode"], metric["data_frequency"]) == (  # noqa: S101
            "periodic",
            "15min",
        )
        assert metric["value_dimensions"] == [  # noqa: S101
            {
                "column": "value",
                "unit": "cm",
                "measurement": "water level",
                "value_data_type": "float",
                "description": "Relative to the gauge zero of 42.713 m. ü. NHN",
            }
        ]
        assert metric["inherited"]["latitude"] == BONN["latitude"]  # noqa: S101
        assert metric["inherited"]["water_longname"] == "RHEIN"  # noqa: S101

    @pytest.mark.usefixtures("pegelonline")
    def test_discharge_metadata():
        timeseries = main(
            station="BONN",
            timestampFrom="2026-03-29T00:00:00+00:00",
            timestampTo="2026-03-29T02:00:00+00:00",
            measurement="Q",
        )["timeseries"]

        assert check_metadata_conventions(timeseries) == []  # noqa: S101
        assert timeseries.attrs["metrics"][0]["value_dimensions"] == [  # noqa: S101
            {
                "column": "value",
                "unit": "m³/s",
                "measurement": "discharge",
                "value_data_type": "float",
            }
        ]


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "station",
            "filters": {"value": "593647aa-9fea-43ec-a7d6-6476a76ae868"},
        },
        {"workflow_input_name": "timestampFrom", "filters": {"value": "now - 15d"}},
        {"workflow_input_name": "timestampTo", "filters": {"value": "now"}},
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
        {"workflow_input_name": "timestampFrom", "filters": {"value": "now - 15d"}},
        {"workflow_input_name": "timestampTo", "filters": {"value": "now"}},
        {
            "workflow_input_name": "measurement",
            "use_default_value": True,
            "filters": {"value": "W"},
        },
    ]
}


# %%
