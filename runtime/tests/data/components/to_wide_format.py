"""Documentation for to Wide Format

# to Wide Format

## Description
Uses the pandas pivot method to convert a MultiTsFrame to a wide format DataFrame.

## Inputs
* **multitsframe** (Pandas DataFrame): The input DataFrame in the format of a MultiTSFrame: The DataFrame should contain the columns "timestamp", "metric", "value", and possibly more
(e.g. "longitude", "latitude"). The timestamp column should have dtype datetime64[ns, UTC], the "metric" column dtype string, and all other columns dtype float64.
* **handle_multiple_value_columns** (String):  Should be one of ["drop", "flatten", "hierarchical"]. Use this parameter to specify how to handle columns additional to "timestamp", "metric", and "value" (e.g. "longitude", "latitude"). If this parameter is set to "drop", additional columns are ignored. Otherwise a MultiIndex is constructed. If "hierarchical", the MultiIndex is left hierarchical, if "flatten" it's flattened to a one-level index using the flattening_delimiter (e.g., "value.a", "value.b", "value.c", "longitude.a", ...). Default: "drop".
* **flattening_delimiter** (String): The delimiter used to flatten the index if handle_multiple_value_columns is "flatten". Default: ".".

## Outputs
* **wide_format_timeseries_dataframe** (Pandas DataFrame): The output DataFrame in wide format with one column for each metric if handle_multiple_value_columns = "drop" or multiple columns for each metric otherwise.

## Details
Uses the pandas pivot method to convert a MultiTsFrame to a wide format DataFrame.

The input multitsframe is required to be a MultiTsFrame, that is, to contain a column "timestamp" of dtype datetime64[ns], a column "metric" of dtype str containing metric names, a column "value" of dtype float64, and possible more columns such as "longitude" and "latitude". Those additional columns are handled depending on the parameter handle_multiple_value_columns:

If it is "drop", all columns except "timestamp", "metric", "value" are dropped and the output DataFrame contains one column "timestamp" of dtype datetime64[ns] and several other columns of dtype float64 named after the metrics ("a", "b", ...).
If it is "hierarchical", the output dataframe has a hierarchical column index with "timestamp" and the other column names of the input MultiTsFrame on level 0 and for each of these other column names the metric names on level 1. To illustrate, the column index will look like this: [("timestamp", ""), ("value", "a"), ("value", "b"), "("value", "c"), ("longitude", "a"), ("longitude", "b"), ...].
If it is "flatten", the same column index is constructed as for "hierarchical", but then it is flattened to a one-level index using the flattening delimiter, for example: ["timestamp", "value.a", "value.b", "value.c", "longitude.a", "longitude.b", ...].

If there is a timestamp where not all metrics have a value, the corresponding positions in the output DataFrame are filled with NaN.
Raises a ComponentInputValidationException if the inputs are ill-formatted or conflicting.
"""

import numpy as np
import pandas as pd

from hdutils import (
    ComponentInputValidationException,
    parse_value,  # noqa: E402
)

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "multitsframe": {"data_type": "MULTITSFRAME"},
        "handle_multiple_value_columns": {
            "data_type": "STRING",
            "default_value": "drop",
        },
        "flattening_delimiter": {"data_type": "STRING", "default_value": "."},
    },
    "outputs": {
        "wide_format_timeseries_dataframe": {"data_type": "DATAFRAME"},
    },
    "name": "to Wide Format",
    "category": "Connectors",
    "description": "Uses the pandas pivot funtion to convert a MultiTsFrame to a wide format DataFrame.",  # noqa: E501
    "version_tag": "1.0.0",
    "id": "327fc07a-1b3f-4c99-a9aa-0f9b2130cdef",
    "revision_group_id": "c12c96de-ab43-4b05-991b-be01024ea580",
    "state": "RELEASED",
    "released_timestamp": "2024-11-19T15:32:29.865273+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, multitsframe, handle_multiple_value_columns="drop", flattening_delimiter="."):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    # "value" must be in the columns
    if "value" not in multitsframe.columns:
        raise ComponentInputValidationException(
            'There is no column named "value" in the MultiTsFrame passed to multitsframe, but there should be.',
            invalid_component_inputs=["multitsframe"],
        )

    # handle_multiple_value_columns parameter must be in {"drop", "flatten", "hierarchical"}
    if handle_multiple_value_columns not in {"drop", "flatten", "hierarchical"}:
        raise ComponentInputValidationException(
            f'{handle_multiple_value_columns} is not a valid value for the handle_multiple_value_columns parameter. It should be set to "drop", "flatten", or "hierarchical" (default: "drop").',
            invalid_component_inputs=["handle_multiple_value_columns"],
        )

    # determine columns for the values of the pivoted dataframe
    if handle_multiple_value_columns == "drop":
        value_cols = "value"
    else:
        value_cols = [col for col in multitsframe.columns if col not in ["timestamp", "metric"]]

    # convert "metrics" column to dtype object instead of string, otherwise the column index of the resulting dataframe has dtype string, which is not standard
    multitsframe["metric"] = multitsframe["metric"].astype(object)

    # pivot mtsf putting the timestamp column as index and unique entries of the metric column as columns
    pivoted_df = multitsframe.pivot_table(
        index="timestamp", columns="metric", values=value_cols, sort=False
    ).reset_index()

    # flatten index if required
    if handle_multiple_value_columns == "flatten":
        pivoted_df.columns = [
            flattening_delimiter.join(col) if col[0] != "timestamp" else "timestamp"
            for col in pivoted_df.columns.to_numpy()
        ]

    # reset names of column index
    pivoted_df.columns.names = [None] * pivoted_df.columns.nlevels

    # sort dataframe and reset index
    pivoted_df = pivoted_df.sort_values(by="timestamp").reset_index(drop=True)

    return {"wide_format_timeseries_dataframe": pivoted_df}


# Testing
try:
    import pytest
except ImportError:
    pass
else:
    # Fixtures
    @pytest.fixture
    def multitsframe():
        long_mtsf = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(
                    [
                        "2019-08-01T15:45:36.000Z",
                        "2019-08-01T15:45:36.000Z",
                        "2019-08-01T15:45:36.000Z",
                        "2019-08-01T15:48:36.000Z",
                        "2019-08-01T15:48:36.000Z",
                        "2019-08-01T15:51:36.000Z",
                        "2019-08-01T15:51:36.000Z",
                    ],
                    format="%Y-%m-%dT%H:%M:%S.%fZ",
                ).tz_localize("UTC"),
                "metric": pd.Series(["a", "b", "c", "a", "b", "a", "c"], dtype=str),
                "value": [1.1, 10.0, -3.5, 1.2, 20.0, 1.3, -5.0],
                "longitude": [111.111111] * 7,
                "latitude": [11.111111] * 7,
            }
        )

        return long_mtsf

    @pytest.fixture
    def wide_format_timeseries_dataframe():
        timestamp = pd.to_datetime(
            [
                "2019-08-01T15:45:36.000Z",
                "2019-08-01T15:48:36.000Z",
                "2019-08-01T15:51:36.000Z",
            ],
            format="%Y-%m-%dT%H:%M:%S.%fZ",
        ).tz_localize("UTC")
        value_a = [1.1, 1.2, 1.3]
        value_b = [10.0, 20.0, np.nan]
        value_c = [-3.5, np.nan, -5.0]
        longitude_a = [111.111111] * 3
        longitude_b = [111.111111, 111.111111, np.nan]
        longitude_c = [111.111111, np.nan, 111.111111]
        latitude_a = [11.111111] * 3
        latitude_b = [11.111111, 11.111111, np.nan]
        latitude_c = [11.111111, np.nan, 11.111111]

        df_drop = pd.DataFrame(
            {
                "timestamp": timestamp,
                "a": value_a,
                "b": value_b,
                "c": value_c,
            }
        )

        df_flatten = pd.DataFrame(
            {
                "timestamp": timestamp,
                "value.a": value_a,
                "value.b": value_b,
                "value.c": value_c,
                "longitude.a": longitude_a,
                "longitude.b": longitude_b,
                "longitude.c": longitude_c,
                "latitude.a": latitude_a,
                "latitude.b": latitude_b,
                "latitude.c": latitude_c,
            }
        )

        df_hierarchical = pd.DataFrame(
            {
                ("timestamp", ""): timestamp,
                ("value", "a"): value_a,
                ("value", "b"): value_b,
                ("value", "c"): value_c,
                ("longitude", "a"): longitude_a,
                ("longitude", "b"): longitude_b,
                ("longitude", "c"): longitude_c,
                ("latitude", "a"): latitude_a,
                ("latitude", "b"): latitude_b,
                ("latitude", "c"): latitude_c,
            }
        )

        return {
            "drop": df_drop,
            "flatten": df_flatten,
            "hierarchical": df_hierarchical,
        }

    def test_run_from_test_wiring(wide_format_timeseries_dataframe):
        kwargs = {
            inp_wiring["workflow_input_name"]: parse_value(
                inp_wiring["filters"]["value"],
                COMPONENT_INFO["inputs"][inp_wiring["workflow_input_name"]]["data_type"],
                nullable=True,
            )
            for inp_wiring in TEST_WIRING_FROM_PY_FILE_IMPORT["input_wirings"]
        }

        output_df = main(**kwargs)["wide_format_timeseries_dataframe"]
        control_df = wide_format_timeseries_dataframe[kwargs["handle_multiple_value_columns"]]

        if not output_df.equals(control_df):
            pytest.fail(f"Expected \n {control_df} \n but got \n {output_df}")

    def test_run_with_multicols(multitsframe, wide_format_timeseries_dataframe):
        for multcols in ["drop", "flatten", "hierarchical"]:
            output_df = main(
                multitsframe=multitsframe,
                handle_multiple_value_columns=multcols,
                flattening_delimiter=".",
            )["wide_format_timeseries_dataframe"]

            control_df = wide_format_timeseries_dataframe[multcols]

            if not output_df.equals(control_df):
                pytest.fail(f"Expected \n {control_df} \n but got \n {output_df}")

    def test_run_with_invalid_multitsframe(multitsframe):
        invalid_mtsf = multitsframe.rename(columns={"value": "not_value"})
        with pytest.raises(ComponentInputValidationException):
            main(multitsframe=invalid_mtsf)

    def test_run_with_invalid_handle_multiple_value_columns(multitsframe):
        with pytest.raises(ComponentInputValidationException):
            main(
                multitsframe=multitsframe,
                handle_multiple_value_columns="invalid",
            )


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "multitsframe",
            "filters": {
                "value": '{\n    "timestamp": [\n        "2019-08-01T15:45:36.000Z",\n        "2019-08-01T15:45:36.000Z",\n        "2019-08-01T15:45:36.000Z",\n        "2019-08-01T15:48:36.000Z",\n        "2019-08-01T15:48:36.000Z",\n        "2019-08-01T15:51:36.000Z",\n        "2019-08-01T15:51:36.000Z"\n    ],\n    "value": [\n        1.1,\n        10,\n        -3.5,\n        1.2,\n        20,\n        1.3,\n        -5\n    ],\n    "metric": [\n        "a",\n        "b",\n        "c",\n        "a",\n        "b",\n        "a",\n        "c"\n    ],\n    "longitude": [\n        "111.111111",\n        "111.111111",\n        "111.111111",\n        "111.111111",\n        "111.111111",\n        "111.111111",\n        "111.111111"\n    ],\n        "latitude": [\n        "11.111111",\n        "11.111111",\n        "11.111111",\n        "11.111111",\n        "11.111111",\n        "11.111111",\n        "11.111111"\n    ]\n}'
            },
        },
        {
            "workflow_input_name": "handle_multiple_value_columns",
            "use_default_value": True,
            "filters": {"value": "drop"},
        },
        {
            "workflow_input_name": "flattening_delimiter",
            "use_default_value": True,
            "filters": {"value": "."},
        },
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "multitsframe",
            "filters": {
                "value": '{\n    "timestamp": [\n        "2019-08-01T15:45:36.000Z",\n        "2019-08-01T15:45:36.000Z",\n        "2019-08-01T15:45:36.000Z",\n        "2019-08-01T15:48:36.000Z",\n        "2019-08-01T15:48:36.000Z",\n        "2019-08-01T15:51:36.000Z",\n        "2019-08-01T15:51:36.000Z"\n    ],\n    "value": [\n        1.1,\n        10,\n        -3.5,\n        1.2,\n        20,\n        1.3,\n        -5\n    ],\n    "metric": [\n        "a",\n        "b",\n        "c",\n        "a",\n        "b",\n        "a",\n        "c"\n    ],\n    "longitude": [\n        "111.111111",\n        "111.111111",\n        "111.111111",\n        "111.111111",\n        "111.111111",\n        "111.111111",\n        "111.111111"\n    ],\n        "latitude": [\n        "11.111111",\n        "11.111111",\n        "11.111111",\n        "11.111111",\n        "11.111111",\n        "11.111111",\n        "11.111111"\n    ]\n}'
            },
        },
        {
            "workflow_input_name": "handle_multiple_value_columns",
            "use_default_value": True,
            "filters": {"value": "drop"},
        },
        {
            "workflow_input_name": "flattening_delimiter",
            "use_default_value": True,
            "filters": {"value": "."},
        },
    ]
}
