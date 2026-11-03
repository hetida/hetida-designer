"""Documentation for Convert SingleTSFrame to Series

# Convert SingleTSFrame to Series

## Description
Convert one value dimension of a SingleTSFrame into a Series.

## Inputs
* **singletsframe** (SingleTSFrame): The input SingleTSFrame.
* **value_column** (String, optional): The value column (value dimension) to extract. Default: "value".

## Outputs
* **series** (Pandas Series): The output Series with the timestamps as index.

## Details
A SERIES is one-dimensional while a SINGLETSFRAME can have arbitrarily many value dimensions. Therefore exactly one value column has to be selected. If the SingleTSFrame has exactly one value column, that column is used regardless of the **value_column** input.

The "timestamp" column becomes the index of the resulting series. The attributes (`.attrs`) are carried over, since the [metadata conventions](https://hetida.github.io/hetida-designer/user_guide/attached_metadata/) identify the single metric the same way for both types. If the metadata follows the conventions, only the value dimension of the selected value column is kept, renamed to "value". The name of the resulting series is set to `dataset_metadata.single_metric` if available, and to the name of the value column otherwise.

Raises a ComponentInputValidationException if the requested value column is not present and the SingleTSFrame has more than one value column.

## Examples
The json input of a typical call of this component is
```
{
    "singletsframe": {
        "value": [1.0, 1.2],
        "timestamp": [
            "2019-08-01T15:42:36.000Z",
            "2019-08-01T15:45:36.000Z"
        ]
    },
    "value_column": "value"
}
```
"""

import copy

import pandas as pd
from hdhelpers.metadata import attrs_to_json, read_metadata, set_metadata

from hdutils import ComponentInputValidationException

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "singletsframe": {"data_type": "SINGLETSFRAME"},
        "value_column": {"data_type": "STRING", "default_value": "value"},
    },
    "outputs": {
        "series": {"data_type": "SERIES"},
    },
    "name": "Convert SingleTSFrame to Series",
    "category": "Connectors",
    "description": "Convert one value dimension of a SingleTSFrame into a Series",
    "version_tag": "1.0.0",
    "id": "ccde0c5c-28e8-4184-8571-6310701027cf",
    "revision_group_id": "bd630510-726b-4d51-b55f-3bdce2da9c37",
    "state": "RELEASED",
    "released_timestamp": "2026-08-05T10:00:00+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, singletsframe, value_column="value"):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    value_columns = [column for column in singletsframe.columns if column != "timestamp"]

    if len(value_columns) == 1:
        selected_column = value_columns[0]
    elif value_column in value_columns:
        selected_column = value_column
    else:
        raise ComponentInputValidationException(
            f'The value column "{value_column}" is not one of the value columns '
            f"{value_columns} of the provided SingleTSFrame, which has more than one "
            "value column, so no unambiguous choice is possible.",
            invalid_component_inputs=["value_column"],
        )

    meta = read_metadata(singletsframe, "SINGLETSFRAME")
    if meta is not None and selected_column in {
        value_dimension.column for value_dimension in meta.metric().value_dimensions
    }:
        series_meta = meta.as_series(selected_column)
        attrs = copy.deepcopy(singletsframe.attrs)
    else:
        # carried over as JSON, also metadata of the SINGLETSFRAME without value dimension of
        # the selected column, which is no metadata of a SERIES
        series_meta = None
        attrs = copy.deepcopy(attrs_to_json(singletsframe.attrs) if singletsframe.attrs else {})

    series_name = selected_column
    dataset_metadata = attrs.get("dataset_metadata")
    if series_meta is not None:
        series_name = series_meta.dataset_metadata.single_metric
    elif isinstance(dataset_metadata, dict) and dataset_metadata.get("single_metric") is not None:
        series_name = dataset_metadata["single_metric"]

    series = pd.Series(
        singletsframe[selected_column].to_numpy(),
        index=pd.Index(singletsframe["timestamp"], name="timestamp"),
        name=series_name,
    ).sort_index()
    series.attrs = attrs
    if series_meta is not None:
        set_metadata(series, series_meta)

    return {"series": series}


# Testing
try:
    import pytest
except ImportError:
    pass
else:
    from hdhelpers.metadata import META_KEY, attach_metadata, check_metadata_conventions

    SINGLETSFRAME_METADATA = {
        "dataset_metadata": {
            "metric_key": "id",
            "single_metric": "abc.temp",
            "queried_metrics": ["abc.temp"],
            "ref_interval_start_timestamp": "2019-08-01T15:00:00Z",
            "ref_interval_end_timestamp": "2019-08-01T16:00:00Z",
            "ref_interval_type": "closed",
        },
        "metrics": [
            {
                "id": "abc.temp",
                "name": "Temperature",
                "value_dimensions": [
                    {"column": "value", "unit": "°C", "measurement": "temperature"},
                    {"column": "state", "unit": None, "measurement": None},
                ],
            }
        ],
    }

    @pytest.fixture
    def singletsframe():
        singletsframe = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(
                    ["2019-08-01T15:45:36.000Z", "2019-08-01T15:42:36.000Z"], utc=True
                ),
                "value": [1.2, 1.0],
                "state": ["ok", "suspicious"],
            }
        )
        singletsframe.attrs = {"dataset_metadata": {"single_metric": "abc.temp"}}
        return singletsframe

    def test_extracts_requested_value_column(singletsframe):
        series = main(singletsframe=singletsframe, value_column="value")["series"]

        assert list(series) == [1.0, 1.2]  # noqa: S101
        assert series.name == "abc.temp"  # noqa: S101
        assert str(series.index.tz) == "UTC"  # noqa: S101
        assert series.attrs["dataset_metadata"]["single_metric"] == "abc.temp"  # noqa: S101

    def test_extracts_other_value_column(singletsframe):
        series = main(singletsframe=singletsframe, value_column="state")["series"]

        assert list(series) == ["suspicious", "ok"]  # noqa: S101

    def test_single_value_column_is_used_regardless(singletsframe):
        one_dimensional = singletsframe.drop(columns=["state"])
        one_dimensional.attrs = {}

        series = main(singletsframe=one_dimensional, value_column="does_not_exist")["series"]

        assert list(series) == [1.0, 1.2]  # noqa: S101
        assert series.name == "value"  # noqa: S101

    @pytest.mark.parametrize("attached", [False, True])
    def test_metadata_following_conventions_is_converted(singletsframe, attached):
        singletsframe.attrs = copy.deepcopy(SINGLETSFRAME_METADATA)
        if attached:
            attach_metadata(singletsframe)

        series = main(singletsframe=singletsframe, value_column="state")["series"]

        assert series.name == "abc.temp"  # noqa: S101
        assert set(series.attrs) == {META_KEY}  # noqa: S101
        assert check_metadata_conventions(series) == []  # noqa: S101
        meta = read_metadata(series, "SERIES", required=True)
        # only the value dimension of the selected column, as "value"
        assert [vd.column for vd in meta.metric().value_dimensions] == ["value"]  # noqa: S101
        assert meta.unit() is None  # noqa: S101

    def test_metadata_without_value_dimension_of_the_column_is_carried_over(singletsframe):
        singletsframe.attrs = copy.deepcopy(SINGLETSFRAME_METADATA)
        attach_metadata(singletsframe)
        singletsframe["score"] = [0.1, 0.2]

        series = main(singletsframe=singletsframe, value_column="score")["series"]

        assert series.attrs == SINGLETSFRAME_METADATA  # noqa: S101
        assert series.name == "abc.temp"  # noqa: S101

    def test_ambiguous_choice_raises(singletsframe):
        with pytest.raises(ComponentInputValidationException):
            main(singletsframe=singletsframe, value_column="does_not_exist")


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "singletsframe",
            "filters": {
                "value": '{\n    "value": [\n        1,\n        1.2,\n        0.5\n    ],\n    "timestamp": [\n        "2019-08-01T15:42:36.000Z",\n        "2019-08-01T15:45:36.000Z",\n        "2019-08-01T15:48:36.000Z"\n    ]\n}'
            },
        },
        {
            "workflow_input_name": "value_column",
            "use_default_value": True,
            "filters": {"value": "value"},
        },
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "singletsframe",
            "filters": {
                "value": '{\n    "value": [\n        1,\n        1.2,\n        0.5\n    ],\n    "timestamp": [\n        "2019-08-01T15:42:36.000Z",\n        "2019-08-01T15:45:36.000Z",\n        "2019-08-01T15:48:36.000Z"\n    ]\n}'
            },
        },
        {
            "workflow_input_name": "value_column",
            "use_default_value": True,
            "filters": {"value": "value"},
        },
    ]
}
