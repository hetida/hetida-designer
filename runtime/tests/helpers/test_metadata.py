"""hetdesrun.helpers.metadata, the thin wrappers over hdhelpers.metadata"""

from copy import deepcopy
from typing import Any

import pandas as pd
import pytest
from hdhelpers.metadata import META_KEY, attach_metadata

from hetdesrun.helpers.metadata import (
    get_display_names,
    get_measurements,
    get_metric_info,
    get_series_display_name,
    get_series_measurement,
    get_series_name,
    get_series_short_display_name,
    get_series_unit,
    get_singlets_display_names,
    get_singlets_measurements,
    get_singlets_metric_info,
    get_singlets_names,
    get_singlets_short_display_names,
    get_singlets_units,
    get_units,
    get_value_dimension_info,
)

DATASET_METADATA: dict[str, Any] = {
    "metric_key": "id",
    "ref_interval_start_timestamp": "2026-10-18T00:00:00Z",
    "ref_interval_end_timestamp": "2026-10-19T00:00:00Z",
    "ref_interval_type": "closed",
}

MULTITSFRAME_METADATA: dict[str, Any] = {
    "dataset_metadata": DATASET_METADATA | {"queried_metrics": ["first", "second"]},
    "value_dimensions_shared": [
        {"column": "pressure", "name": "shared pressure name", "measurement": "pressure"}
    ],
    "metrics": [
        {
            "id": "first",
            "name": "first name",
            "display_name": "first display name",
            "external_id": "external_first",
            "value_dimensions": [
                {"column": "temp", "unit": "°C", "measurement": "temperature"},
                {"column": "pressure", "unit": "bar", "measurement": None},
            ],
        },
        {
            "id": "second",
            "name": "second name",
            "external_id": "external_second",
            "inherited": {"site": "north"},
            "value_dimensions": [
                {"column": "temp", "unit": "K", "measurement": None},
                {
                    "column": "pressure",
                    "display_name": "second's pressure",
                    "unit": None,
                    "measurement": None,
                },
            ],
        },
    ],
}


def as_attached(obj: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    attached = obj.copy()
    attached.attrs = deepcopy(obj.attrs)
    assert attach_metadata(attached) is not None
    return attached


@pytest.fixture(params=["plain", "attached"])
def multitsframe(request: pytest.FixtureRequest) -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2026-10-18T06:00:00Z"] * 2),
            "metric": ["first", "second"],
            "temp": [21.5, 295.0],
            "pressure": [1.0, 2.0],
        }
    )
    frame.attrs = deepcopy(MULTITSFRAME_METADATA)
    return frame if request.param == "plain" else as_attached(frame)


@pytest.fixture(params=["plain", "attached"])
def singletsframe(request: pytest.FixtureRequest) -> pd.DataFrame:
    frame = pd.DataFrame(
        {"timestamp": pd.to_datetime(["2026-10-18T06:00:00Z"]), "temp": [21.5], "pressure": [1.0]}
    )
    frame.attrs = {
        "dataset_metadata": DATASET_METADATA
        | {"single_metric": "first", "queried_metrics": ["first"]},
        "value_dimensions_shared": deepcopy(MULTITSFRAME_METADATA["value_dimensions_shared"]),
        "metrics": deepcopy(MULTITSFRAME_METADATA["metrics"][:1]),
    }
    return frame if request.param == "plain" else as_attached(frame)


@pytest.fixture(params=["plain", "attached"])
def series(request: pytest.FixtureRequest) -> pd.Series:
    ser = pd.Series([1.5], index=pd.to_datetime(["2026-10-18T06:00:00Z"]))
    ser.attrs = {
        "dataset_metadata": DATASET_METADATA
        | {"single_metric": "level", "queried_metrics": ["level"]},
        "metrics": [
            {
                "id": "level",
                "name": "Water level",
                "short_display_name": "Level",
                "value_dimensions": [{"column": "value", "unit": "m", "measurement": "level"}],
            }
        ],
    }
    return ser if request.param == "plain" else as_attached(ser)


def test_multitsframe_value_dimensions(multitsframe: pd.DataFrame) -> None:
    units = get_units(multitsframe)
    assert get_value_dimension_info(multitsframe, "unit") == units
    assert units["first"]["temp"] == "°C"
    assert units["second"]["pressure"] is None
    assert units["unknown metric"]["temp"] is None
    # the shared value dimension as fallback
    assert get_measurements(multitsframe)["first"]["pressure"] == "pressure"
    assert get_display_names(multitsframe)["second"]["pressure"] == "second's pressure"
    assert get_display_names(multitsframe)["first"]["pressure"] == "shared pressure name"


def test_multitsframe_metric_info(multitsframe: pd.DataFrame) -> None:
    assert get_metric_info(multitsframe, "external_id") == {
        "first": "external_first",
        "second": "external_second",
    }
    assert get_metric_info(multitsframe, "site")["second"] == "north"
    assert get_metric_info(multitsframe, "inherited.site")["second"] == "north"
    assert get_metric_info(multitsframe, "external_id")["unknown metric"] is None


def test_singletsframe(singletsframe: pd.DataFrame) -> None:
    units = get_singlets_units(singletsframe)
    assert (units["temp"], units["pressure"], units["unknown column"]) == ("°C", "bar", None)
    assert get_singlets_names(singletsframe)["pressure"] == "shared pressure name"
    # only the value dimension "value" falls back to the metric
    assert get_singlets_display_names(singletsframe)["temp"] is None
    assert get_singlets_short_display_names(singletsframe)["pressure"] == "shared pressure name"
    assert get_singlets_measurements(singletsframe)["temp"] == "temperature"
    assert get_singlets_metric_info(singletsframe, "external_id") == "external_first"


def test_series(series: pd.Series) -> None:
    assert get_series_unit(series) == "m"
    assert get_series_name(series) == "Water level"
    assert get_series_display_name(series) == "Water level"
    assert get_series_short_display_name(series) == "Level"
    assert get_series_measurement(series) == "level"


def test_metadata_not_following_conventions_gives_no_information() -> None:
    # e.g. an older structure
    frame = pd.DataFrame({"timestamp": [], "metric": [], "value": []})
    frame.attrs = {"metrics": {"first": {"unit": "m"}}}
    ser = pd.Series([1.0])
    ser.attrs = {"single_metric_metadata": {"structured_metadata": {"metric": {"unit": "m"}}}}

    assert get_units(frame)["first"]["value"] is None
    assert get_metric_info(frame, "unit")["first"] is None
    assert get_series_unit(ser) is None
    assert get_singlets_units(frame)["value"] is None
    assert get_singlets_metric_info(frame, "unit") is None


def test_attached_metadata_of_another_data_type_is_used(singletsframe: pd.DataFrame) -> None:
    attached = as_attached(singletsframe)
    # e.g. a Series taken from a SINGLETSFRAME shares its metadata
    temp = attached["temp"]

    assert META_KEY in temp.attrs
    assert get_value_dimension_info(temp, "unit")["first"]["temp"] == "°C"
