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

The "timestamp" column becomes the index of the resulting series. The attributes (`.attrs`) are carried over unchanged, since the [metadata conventions](https://hetida.github.io/hetida-designer/user_guide/attached_metadata/) identify the single metric the same way for both types. The name of the resulting series is set to `dataset_metadata.single_metric` if available, and to the name of the value column otherwise.

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

    attrs = copy.deepcopy(singletsframe.attrs) if singletsframe.attrs else {}

    series_name = selected_column
    dataset_metadata = attrs.get("dataset_metadata")
    if isinstance(dataset_metadata, dict) and dataset_metadata.get("single_metric") is not None:
        series_name = dataset_metadata["single_metric"]

    series = pd.Series(
        singletsframe[selected_column].to_numpy(),
        index=pd.Index(singletsframe["timestamp"], name="timestamp"),
        name=series_name,
    ).sort_index()
    series.attrs = attrs

    return {"series": series}


# Testing
try:
    import pytest
except ImportError:
    pass
else:

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
