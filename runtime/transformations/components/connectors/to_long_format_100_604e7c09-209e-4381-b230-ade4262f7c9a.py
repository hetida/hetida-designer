"""Documentation for to Long Format

# to Long Format

## Description
Uses the pandas melt method to convert a wide format timeseries DataFrame to a MultiTsFrame, i.e. a DataFrame representing timeseries data in long format.

## Inputs
* **wide_format_timeseries_dataframe** (Pandas DataFrame): The input DataFrame which should consist of a timestamp column with dtype datetime64[ns,UTC] and for each metric one column (e.g., "a", "b", "c") or multiple columns (e.g., "value.a", "value.b", "value.c", "longitude.a", "longitude.b", "longitude.c", ...) with dtype float64.
* **handle_multiple_value_columns_per_metric** (String): This parameter corresponds to the "handle_multiple_value_columns" parameter from the to Wide Format component and has possible values "drop", "flatten" or "hierarchical". Use this parameter to specify if the passed DataFrame has only one column for each metric (in this case use "drop") or multiple, and if it has multiple, whether the column index is flattened ("timestamp", "value.a", ...) or hierarchical (MultiIndex([("timestamp", ""), ("value", "a"), ...]). Default: "drop".
* **flattening_delimiter** (String): In case wide_format_timeseries_dataframe has a flattened column index, specify the delimiter (e.g., "."). Default: ".".

## Outputs
* **multitsframe** (Pandas DataFrame): The output MultiTsFrame constructed from the DataFrame.

## Details
Uses the pandas melt method to convert a wide format DataFrame to a long format MultiTsFrame.

In the input wide_format_timeseries_dataframe, the column "timestamp" of dtype datetime64[ns] is always required. Additional columns of dtype float64 are required depending on the value of handle_multiple_value_columns_per_metric:
If it is "drop", a column for each metric ("temperature", "humidity", ...) is expected.
If it is "hierarchical", a hierarchical column index is expected, containing "timestamp", "value", and other properties (e.g., "longitude", "latitude") on level 0 and for each of these index level 0 values except timestamp the metric names on level 1. To illustrate, the column index should look like this: [("timestamp", ""), ("value", "a"), ("value", "b"), "("value", "c"), ("longitude", "a"), ("longitude", "b"), ...].
If it is "flatten", the same columns are expected as for "hierarchical" but flattened to a one-level index using the flattening delimiter, for example: ["timestamp", "value.a", "value.b", "value.c", "longitude.a", "longitude.b", ...].

The output is a MultiTsFrame containing one column "timestamp" of dtype datetime64[ns], one column "metric" of dtype str containing the metric names that were in the columns of the input DataFrame, one column "value" of dtype float containing the values of the respective metric at that respective point of time, and depending on the handle_multiple_columns_per_metric parameter possibly more columns (such as "longitude", "latitude", ...).

Raises a ComponentInputValidationException if the inputs are ill-formatted or conflicting.

"""

import re

import numpy as np
import pandas as pd

from hdutils import (
    ComponentInputValidationException,
    parse_value,  # noqa: E402
)


# this function checks whether inputs are as required, if not raises an Exception
def validate_inputs(
    wide_format_timeseries_dataframe,
    handle_multiple_value_columns_per_metric,
    flattening_delimiter,
):
    # check whether wide_format_timeseries_dataframe has "timestamp" column that is appropriate for mtsf
    if not "timestamp" in wide_format_timeseries_dataframe.columns:
        raise ComponentInputValidationException(
            'There is no column "timestamp" in the DataFrame passed to wide_format_timeseries_dataframe, but there should be.',
            invalid_component_inputs=["wide_format_timeseries_dataframe"],
        )

    if wide_format_timeseries_dataframe["timestamp"].isna().any():
        raise ComponentInputValidationException(
            'No missing values are allowed in the column "timestamp" of a MulitTSFrame.',
            invalid_component_inputs=["wide_format_timeseries_dataframe"],
        )

    if wide_format_timeseries_dataframe["timestamp"].dtype != "datetime64[ns, UTC]":
        raise ComponentInputValidationException(
            (
                f'{wide_format_timeseries_dataframe["timestamp"].dtype} is an inappropriate dtype for the "timestamp"'
                " column of a MultiTSFrame. It should be datetime64[ns, UTC] instead."
            ),
            invalid_component_inputs=["wide_format_timeseries_dataframe"],
        )

    # handle_multiple_value_columns_per_metric parameter must be in ["drop", "flatten", "hierarchical"]
    if handle_multiple_value_columns_per_metric not in {
        "drop",
        "flatten",
        "hierarchical",
    }:
        raise ComponentInputValidationException(
            f'"{handle_multiple_value_columns_per_metric}" is not a valid value for the handle_multiple_columns parameter. It should be set to "drop", "flatten", or "hierarchical" (default: "drop").',
            invalid_component_inputs=["handle_multiple_value_columns_per_metric"],
        )

    # columns must have the appropriate number of levels for handle_multiple_value_columns_per_metric parameter
    appr_levels = {"drop": 1, "flatten": 1, "hierarchical": 2}
    if (a := appr_levels[handle_multiple_value_columns_per_metric]) != (
        n := wide_format_timeseries_dataframe.columns.nlevels
    ):
        raise ComponentInputValidationException(
            (
                f"handle_multiple_value_columns_per_metric = {handle_multiple_value_columns_per_metric} requires the column index"
                f"of wide_format_timeseries_dataframe to have {a} levels, but it has {n}."
            ),
            invalid_component_inputs=[
                "wide_format_timeseries_dataframe",
                "handle_multiple_value_columns_per_metric",
            ],
        )

    # check if dtypes of all columns except timestamp are float64
    level = None if handle_multiple_value_columns_per_metric != "hierarchical" else 0
    other_dtypes = set(
        wide_format_timeseries_dataframe.drop("timestamp", axis=1, level=level).dtypes.values
    )
    if other_dtypes != {np.dtype("float64")}:
        raise ComponentInputValidationException(
            f'All columns except "timestamp" should be of dtype float64, not {other_dtypes}.',
            invalid_component_inputs=["wide_format_timeseries_dataframe"],
        )

    # check if flattening delimiter is in each column name except timestamp
    if handle_multiple_value_columns_per_metric == "flatten":
        should_contain_delimiter = (
            wide_format_timeseries_dataframe.copy().drop("timestamp", axis=1).columns
        )
        if not all(should_contain_delimiter.str.contains(re.escape(flattening_delimiter))):
            raise ComponentInputValidationException(
                (
                    f'All columns except "timestamp" should contain the flattening_delimiter "{flattening_delimiter}"'
                    'if handle_multiple_value_columns_per_metric is set to "flatten", but some do not.'
                ),
                invalid_component_inputs=[
                    "wide_format_timeseries_dataframe",
                    "flattening_delimiter",
                ],
            )


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "wide_format_timeseries_dataframe": {"data_type": "DATAFRAME"},
        "handle_multiple_value_columns_per_metric": {
            "data_type": "STRING",
            "default_value": "drop",
        },
        "flattening_delimiter": {"data_type": "STRING", "default_value": "."},
    },
    "outputs": {
        "multitsframe": {"data_type": "MULTITSFRAME"},
    },
    "name": "to Long Format",
    "category": "Connectors",
    "description": "Uses the pandas melt function to convert a wide format DataFrame to a MultiTsFrame.",  # noqa: E501
    "version_tag": "1.0.0",
    "id": "604e7c09-209e-4381-b230-ade4262f7c9a",
    "revision_group_id": "e1dda214-a6d0-4a03-93db-4eae4670b5ca",
    "state": "RELEASED",
    "released_timestamp": "2024-11-19T15:32:23.371423+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(
    *,
    wide_format_timeseries_dataframe,
    handle_multiple_value_columns_per_metric="drop",
    flattening_delimiter=".",
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    # in order to not change the original input dataframe
    wide_format_timeseries_dataframe = wide_format_timeseries_dataframe.copy()

    # check whether inputs are as required, if not raise Exception
    validate_inputs(
        wide_format_timeseries_dataframe,
        handle_multiple_value_columns_per_metric,
        flattening_delimiter,
    )

    # melt wide_format_timeseries_dataframe according to handle_multiple_value_columns_per_metric
    if handle_multiple_value_columns_per_metric == "drop":
        melted_mtsf = wide_format_timeseries_dataframe.melt(
            id_vars="timestamp",
            var_name="metric",
            value_name="value",
        )
        melted_mtsf = melted_mtsf.dropna()
        melted_mtsf = melted_mtsf.sort_values(by=["timestamp", "metric"]).reset_index(drop=True)
    else:
        # flatten column index if it is hierarchical
        if handle_multiple_value_columns_per_metric == "hierarchical":
            wide_format_timeseries_dataframe.columns = [
                (flattening_delimiter.join(col) if col[0] != "timestamp" else "timestamp")
                for col in wide_format_timeseries_dataframe.columns
            ]

        # find out which columns (except "timestamp" and "metric") the new dataframe should consist of
        seen = set()
        new_cols = [
            val
            for col in wide_format_timeseries_dataframe.columns
            if col != "timestamp"
            and (val := col.split(flattening_delimiter, maxsplit=1)[0]) not in seen
            and not seen.add(val)
        ]

        # for each of the new columns melt a df
        melted_list = []
        for col in new_cols:
            melted_df = pd.melt(
                wide_format_timeseries_dataframe,
                id_vars=["timestamp"],
                value_vars=[
                    old_col
                    for old_col in wide_format_timeseries_dataframe.columns
                    if col == old_col.split(flattening_delimiter)[0]
                ],
                var_name="metric",
                value_name=col,
            )

            melted_df["metric"] = melted_df["metric"].str.split(flattening_delimiter).str[1]

            # drop rows with missing values and add melted df to list
            melted_list.append(melted_df.dropna())

        # merge all melted dfs on timestamp and metric
        melted_mtsf = melted_list.pop(0)
        for m in melted_list:
            melted_mtsf = melted_mtsf.merge(m, on=["timestamp", "metric"])

    # convert "metrics" column to dtype str, because it is constructed from the object type column index
    melted_mtsf["metric"] = melted_mtsf["metric"].astype(str)

    # sort and drop index
    melted_mtsf = melted_mtsf.sort_values(by=["timestamp", "metric"]).reset_index(drop=True)

    return {"multitsframe": melted_mtsf}


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

        mtsf_drop = pd.DataFrame(
            {
                "timestamp": timestamp,
                "a": value_a,
                "b": value_b,
                "c": value_c,
            }
        )

        mtsf_flatten = pd.DataFrame(
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

        mtsf_hierarchical = pd.DataFrame(
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
            "drop": mtsf_drop,
            "flatten": mtsf_flatten,
            "hierarchical": mtsf_hierarchical,
        }

    def test_run_from_test_wiring(multitsframe):
        kwargs = {
            inp_wiring["workflow_input_name"]: parse_value(
                inp_wiring["filters"]["value"],
                COMPONENT_INFO["inputs"][inp_wiring["workflow_input_name"]]["data_type"],
                nullable=True,
            )
            for inp_wiring in TEST_WIRING_FROM_PY_FILE_IMPORT["input_wirings"]
        }
        output_mtsf = main(**kwargs)["multitsframe"]
        control_mtsf = multitsframe.drop(["longitude", "latitude"], axis=1)

        if not output_mtsf.equals(control_mtsf):
            pytest.fail(f"Expected \n {control_mtsf} \n but got \n {output_mtsf}")

    def test_run_with_multicols(multitsframe, wide_format_timeseries_dataframe):
        for multcols in ["drop", "flatten", "hierarchical"]:
            output_mtsf = main(
                wide_format_timeseries_dataframe=wide_format_timeseries_dataframe[multcols],
                handle_multiple_value_columns_per_metric=multcols,
                flattening_delimiter=".",
            )["multitsframe"]

            control_mtsf = multitsframe
            if multcols == "drop":
                control_mtsf = control_mtsf.drop(["longitude", "latitude"], axis=1)

            if not output_mtsf.equals(control_mtsf):
                pytest.fail(f"Expected \n {control_mtsf} \n but got \n {output_mtsf}")

    def test_run_with_invalid_timestamp_column_name(wide_format_timeseries_dataframe):
        input_mtsf = wide_format_timeseries_dataframe["drop"].rename(
            columns={"timestamp": "not_timestamp"}
        )

        with pytest.raises(ComponentInputValidationException):
            main(wide_format_timeseries_dataframe=input_mtsf)

    def test_run_with_invalid_timestamp_column_format(wide_format_timeseries_dataframe):
        input_mtsf = wide_format_timeseries_dataframe["drop"]
        input_mtsf["timestamp"] = input_mtsf["timestamp"].astype(str)
        input_mtsf.loc[0, "timestamp"] = "Not a datetime value"

        with pytest.raises(ComponentInputValidationException):
            main(wide_format_timeseries_dataframe=input_mtsf)

    def test_run_with_nat_value_in_timestamp_column(wide_format_timeseries_dataframe):
        input_mtsf = wide_format_timeseries_dataframe["drop"]
        input_mtsf.loc[0, "timestamp"] = pd.NaT

        with pytest.raises(ComponentInputValidationException):
            main(wide_format_timeseries_dataframe=input_mtsf)

    def test_run_with_invalid_handle_multiple_value_columns_per_metric(
        wide_format_timeseries_dataframe,
    ):
        with pytest.raises(ComponentInputValidationException):
            main(
                wide_format_timeseries_dataframe=wide_format_timeseries_dataframe["drop"],
                handle_multiple_value_columns_per_metric="invalid_parameter_value",
            )

    def test_run_with_invalid_column_index_levels(wide_format_timeseries_dataframe):
        parameter_index_levels_invalid = {1: "hierarchical", 2: "flatten"}
        parameter_index_levels_valid = {1: "flatten", 2: "hierarchical"}
        for levels in [1, 2]:
            with pytest.raises(ComponentInputValidationException):
                main(
                    wide_format_timeseries_dataframe=wide_format_timeseries_dataframe[
                        parameter_index_levels_invalid[levels]
                    ],
                    handle_multiple_value_columns_per_metric=parameter_index_levels_valid[levels],
                )

    def test_run_with_missing_flattening_delimiter(
        wide_format_timeseries_dataframe,
    ):
        wide_format_df = wide_format_timeseries_dataframe["flatten"]
        wide_format_df = wide_format_df.rename({"longitude.a": "longitude_a"}, axis=1)
        with pytest.raises(ComponentInputValidationException):
            main(
                wide_format_timeseries_dataframe=wide_format_df,
                handle_multiple_value_columns_per_metric="flatten",
            )


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "wide_format_timeseries_dataframe",
            "filters": {
                "value": '{\n    "timestamp": [\n        "2019-08-01T15:45:36.000Z",\n        "2019-08-01T15:48:36.000Z",\n        "2019-08-01T15:51:36.000Z" ],\n    "a": [\n        1.1,\n        1.2,\n        1.3 ],\n    "b": [\n        10,\n        20,\n        null ],\n    "c": [\n        -3.5,\n        null,\n        -5]\n}'
            },
        },
        {
            "workflow_input_name": "handle_multiple_value_columns_per_metric",
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
            "workflow_input_name": "wide_format_timeseries_dataframe",
            "filters": {
                "value": '{\n    "timestamp": [\n        "2019-08-01T15:45:36.000Z",\n        "2019-08-01T15:48:36.000Z",\n        "2019-08-01T15:51:36.000Z" ],\n    "a": [\n        1.1,\n        1.2,\n        1.3 ],\n    "b": [\n        10,\n        20,\n        null ],\n    "c": [\n        -3.5,\n        null,\n        -5]\n}'
            },
        },
        {
            "workflow_input_name": "handle_multiple_value_columns_per_metric",
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
