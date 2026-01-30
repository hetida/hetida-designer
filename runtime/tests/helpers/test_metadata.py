import json
from copy import deepcopy

import pandas as pd

from hetdesrun.helpers.metadata import get_display_names, get_measurements, get_units

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
            "name": "shared value_dimension pressure name"
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
                    "unit": "C"
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
    df.attrs = old_metadata
    measurements_by_metric = get_measurements(df)

    assert measurements_by_metric["test_channel"] is None
    assert measurements_by_metric["some_other_metric"] == "volume"

    # is a default dict
    assert measurements_by_metric["SOME"] is None


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
