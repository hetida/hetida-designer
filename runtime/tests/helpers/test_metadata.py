import json
from copy import deepcopy

import pandas as pd

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
)

# what the platform currently sends with a single Series:

old_metadata = json.loads(
    """{
    "metrics": {
        "test_channel": {
            "tenantId": "tenant_a",
            "id": "0eeccba1-b38d-48ac-bad7-630a743e241b",
            "name": "Some name",
            "icon": null,
            "type": "FLOAT",
            "unit": "l/min",
            "externalTimeSeriesId": "some_external_id",
            "description": null,
            "measurement": null,
            "visualization": null,
            "virtualChannel": true,
            "aggregationType": "ORIGINAL",
            "aggregationInterval": null,
            "schedulerJob": {
                "id": "some_id"
            },
            "singleTimeseries": true
        },
        "some_other_metric": {
            "unit": "l",
            "measurement": "volume"
        }
    }
}"""
)

metadata_with_value_dimensions = json.loads(
    """{
    "dataset_metadata": {
        "metric_key": "id"
    },
    "value_dimensions_shared": [
        {
            "column": "pressure",
            "unit": "bar",
            "name": "shared value_dimension pressure name",
            "measurement": "pressure"
        },
        {
            "column": "temp",
            "measurement": "temperature"
        }
    ],
    "metrics": [
        {
            "id": "first",
            "external_id": "external_first",
            "unit": "m",
            "display_name": "first display name",
            "value_dimensions": [
                {
                    "column": "temp",
                    "unit": "C",
                    "measurement": "temperature"
                }
            ]
        },
        {
            "id": "second",
            "name": "second name",
            "external_id": "external_second",
            "value_dimensions": [
                {
                    "column": "temp",
                    "unit": "C"
                }
            ]
        },
        {
            "id": "third",
            "external_id": "external_third",
            "measurement": "height",
            "value_dimensions": [
                {
                    "column": "pressure",
                    "display_name": "thirds's pressure"
                }
            ]
        },
        {
            "id": "fourth",
            "external_id": "external_fourth",
            "unit": "l",
            "value_dimensions": [
                {
                    "column": "pressure",
                    "unit" : "Pa"
                }
            ]
        },
        {
            "id": "fifth",
            "external_id": "external_fifth",
            "unit": "l",
            "value_dimensions": [
                {
                    "column": "value",
                    "unit" : "m^3"
                }
            ]
        }
    ]
    }
"""
)


def test_get_multitsframe_units_from_metadata():
    df = pd.DataFrame()
    df.attrs = old_metadata
    units_by_metric_by_value_dimension = get_units(df)

    assert units_by_metric_by_value_dimension["test_channel"]["value"] == "l/min"
    assert units_by_metric_by_value_dimension["some_other_metric"]["value"] == "l"

    # is a default dict
    assert units_by_metric_by_value_dimension["SOME"]["SOME"] is None


def test_get_multitsframe_measurements_from_metadata():
    df = pd.DataFrame()
    df.attrs = metadata_with_value_dimensions
    measurements_by_metric_by_value_dimension = get_measurements(df)

    assert measurements_by_metric_by_value_dimension["first"]["temp"] == "temperature"
    assert measurements_by_metric_by_value_dimension["first"]["value"] is None
    assert measurements_by_metric_by_value_dimension["first"]["pressure"] == "pressure"
    assert measurements_by_metric_by_value_dimension["first"]["NOT OCCURING"] is None
    assert measurements_by_metric_by_value_dimension["NOT OCCURING"]["value"] is None

    assert measurements_by_metric_by_value_dimension["second"]["temp"] == "temperature"

    assert measurements_by_metric_by_value_dimension["third"]["value"] == "height"
    assert measurements_by_metric_by_value_dimension["third"]["pressure"] == "pressure"


def test_get_multitsframe_units_from_metadata_with_value_dimensions():
    df = pd.DataFrame()
    df.attrs = metadata_with_value_dimensions
    units_by_metric_by_value_dimension = get_units(df)

    assert units_by_metric_by_value_dimension["first"]["temp"] == "C"
    assert units_by_metric_by_value_dimension["first"]["value"] == "m"
    assert units_by_metric_by_value_dimension["first"]["NOT OCCURING"] is None
    assert units_by_metric_by_value_dimension["NOT OCCURING"]["value"] is None

    assert units_by_metric_by_value_dimension["second"]["temp"] == "C"
    assert units_by_metric_by_value_dimension["second"]["value"] is None

    assert units_by_metric_by_value_dimension["third"]["pressure"] == "bar"
    assert units_by_metric_by_value_dimension["third"]["value"] is None

    assert units_by_metric_by_value_dimension["fourth"]["pressure"] == "Pa"
    assert units_by_metric_by_value_dimension["fourth"]["value"] == "l"

    assert units_by_metric_by_value_dimension["fifth"]["pressure"] == "bar"
    assert units_by_metric_by_value_dimension["fifth"]["value"] == "m^3"

    # using other metric_key
    metadata_with_value_dimensions_using_other_mertic_key = deepcopy(metadata_with_value_dimensions)
    metadata_with_value_dimensions_using_other_mertic_key["dataset_metadata"]["metric_key"] = (
        "external_id"
    )
    df.attrs = metadata_with_value_dimensions_using_other_mertic_key

    units_by_metric_by_value_dimension = get_units(df)

    assert units_by_metric_by_value_dimension["external_first"]["temp"] == "C"
    assert units_by_metric_by_value_dimension["external_first"]["value"] == "m"
    assert units_by_metric_by_value_dimension["external_first"]["NOT OCCURING"] is None
    assert units_by_metric_by_value_dimension["NOT OCCURING"]["value"] is None

    assert units_by_metric_by_value_dimension["external_second"]["temp"] == "C"
    assert units_by_metric_by_value_dimension["external_second"]["value"] is None

    assert units_by_metric_by_value_dimension["external_third"]["pressure"] == "bar"
    assert units_by_metric_by_value_dimension["external_third"]["value"] is None

    assert units_by_metric_by_value_dimension["external_fourth"]["pressure"] == "Pa"
    assert units_by_metric_by_value_dimension["external_fourth"]["value"] == "l"

    assert units_by_metric_by_value_dimension["external_fifth"]["pressure"] == "bar"
    assert units_by_metric_by_value_dimension["external_fifth"]["value"] == "m^3"


def test_get_multitsframe_display_names_from_metadata_with_value_dimensions():
    df = pd.DataFrame()
    df.attrs = metadata_with_value_dimensions
    display_names_by_metric_by_value_dimension = get_display_names(df)

    assert display_names_by_metric_by_value_dimension["first"]["temp"] is None
    assert display_names_by_metric_by_value_dimension["first"]["value"] == "first display name"
    assert (
        display_names_by_metric_by_value_dimension["first"]["pressure"]
        == "shared value_dimension pressure name"
    )

    assert display_names_by_metric_by_value_dimension["first"]["NOT OCCURING"] is None
    assert display_names_by_metric_by_value_dimension["NOT OCCURING"]["value"] is None

    assert display_names_by_metric_by_value_dimension["second"]["value"] == "second name"
    assert display_names_by_metric_by_value_dimension["second"]["temp"] is None

    assert display_names_by_metric_by_value_dimension["third"]["pressure"] == "thirds's pressure"
    assert display_names_by_metric_by_value_dimension["third"]["temp"] is None


def test_get_metric_info():
    df = pd.DataFrame()
    df.attrs = metadata_with_value_dimensions
    external_ids_by_metric = get_metric_info(df, "external_id")

    assert external_ids_by_metric["UNKNOWN"] is None
    assert external_ids_by_metric["first"] == "external_first"
    assert external_ids_by_metric["second"] == "external_second"


series_metadata_1 = json.loads(
    """{
    "dataset_metadata": {
        "metric_key": "id",
        "single_metric": "series"
    },
    "metrics": [
        {
            "id": "series",
            "external_id": "external_first",
            "unit": "m",
            "name": "first name"
        }
    ]
    }
"""
)

series_metadata_old = json.loads(
    """
{
    "dataset_metadata": {
      "ref_interval_start_timestamp": "2026-02-06T12:45:00Z",
      "ref_interval_end_timestamp": "2026-02-06T12:45:00Z",
      "ref_interval_type": "closed",
      "ref_metric": "Muster Channel",
      "ref_data_frequency": null,
      "ref_data_frequency_offset": null,
      "invalidation_interval_start": null,
      "invalidation_interval_end": null,
      "invalidation_interval_type": null,
      "invalidate_dataset": null,
      "delete_invalidated": null,
      "only_invalidate": null,
      "ref_dataset_discrete": null,
      "invalidation_timestamp": null,
      "new_data_invalidation_date": null
    },
    "single_metric_metadata": {
      "structured_metadata": {
        "metric": {
          "name": "Muster Channel",
          "display_name": null,
          "short_display_name": "muster",
          "description": "*neue Beschreibung",
          "unit": "C°",
          "value_data_type": null,
          "external_id": "raspi_demo.Heizung4.Temperature",
          "channel_id": "67d5fc88-af8f-4901-92d1-cc61090a2023"
        },
        "inherited": {},
        "value_dimensions": {
          "value": {
            "display_name": null,
            "short_display_name": null,
            "description": null,
            "unit": "C°",
            "value_data_type": "float"
          }
        }
      }
    }
  }

"""
)


def test_series_unit():
    s = pd.Series()
    s.attrs = series_metadata_1

    assert get_series_unit(s) == "m"

    assert get_series_name(s) == "first name"
    assert get_series_display_name(s) == "first name"
    assert get_series_short_display_name(s) == "first name"

    assert get_series_measurement(s) is None

    s.attrs = series_metadata_old

    assert get_series_unit(s) == "C°"

    assert get_series_name(s) == "Muster Channel"
    assert get_series_display_name(s) == "Muster Channel"
    assert get_series_short_display_name(s) == "muster"

    assert get_series_measurement(s) is None


singletsframe_metadata = {
    "dataset_metadata": {
        "single_metric": "abc.temp",
        "metric_key": "external_id",
    },
    "metrics": [
        {
            "external_id": "abc.temp",
            "name": "ABC temperature",
            "value_dimensions": [
                {"column": "value", "name": "temperature", "unit": "°C"},
                {"column": "state", "name": "measurement state"},
            ],
        }
    ],
    "value_dimensions_shared": [{"column": "state", "unit": "UNKNOWN"}],
}


def test_singlets_info_by_value_dimension():
    """A SingleTSFrame has one metric, so info is keyed by value dimension only"""
    df = pd.DataFrame()
    df.attrs = singletsframe_metadata

    units = get_singlets_units(df)
    assert units["value"] == "°C"
    assert units["state"] == "UNKNOWN"  # falls back to value_dimensions_shared
    assert units["NOT OCCURING"] is None

    names = get_singlets_names(df)
    assert names["value"] == "temperature"
    assert names["state"] == "measurement state"

    assert get_singlets_display_names(df)["value"] == "temperature"
    assert get_singlets_short_display_names(df)["value"] == "temperature"
    assert get_singlets_measurements(df)["value"] is None


def test_singlets_info_falls_back_to_only_metric_without_single_metric():
    """If single_metric is missing but there is exactly one metric, use that one"""
    df = pd.DataFrame()
    metadata = deepcopy(singletsframe_metadata)
    del metadata["dataset_metadata"]["single_metric"]
    df.attrs = metadata

    assert get_singlets_units(df)["value"] == "°C"


def test_singlets_info_defaults_metric_key_to_id():
    """metric_key is optional per convention and defaults to "id" """
    df = pd.DataFrame()
    df.attrs = {
        "dataset_metadata": {"single_metric": "abc.temp"},
        "metrics": [
            {
                "id": "abc.temp",
                "value_dimensions": [{"column": "value", "unit": "°C"}],
            }
        ],
    }

    assert get_singlets_units(df)["value"] == "°C"


def test_singlets_info_without_metadata():
    df = pd.DataFrame()
    df.attrs = {}

    assert get_singlets_units(df)["value"] is None
    assert get_singlets_metric_info(df, "name") is None


def test_singlets_metric_info():
    df = pd.DataFrame()
    df.attrs = singletsframe_metadata

    assert get_singlets_metric_info(df, "name") == "ABC temperature"
    assert get_singlets_metric_info(df, "external_id") == "abc.temp"
