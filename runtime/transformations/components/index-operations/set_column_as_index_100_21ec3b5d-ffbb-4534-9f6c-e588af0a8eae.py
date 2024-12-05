"""Documentation for Set Column as Index

# Set Column as Index

## Description
Uses the pandas set_index method to set a given column of a DataFrame as its index.

## Inputs
* **df_to_reindex** (Pandas DataFrame): The input DataFrame that will be reindexed.
* **index_column** (String): The name of the column to be set as the new index. Default: "timestamp".

## Outputs
* **reindexed_df** (Pandas DataFrame): The output DataFrame with index_column as the new index.

## Details
Sets index_column as the new index of df_to_reindex, drops that column from the columns of df_to_reindex, and drops the old index.

The index_column is expected not to contain duplicates or missing values. If it does, or if it is not a column of the df_to_reindex, a ComponentInputValidationException is raised.

"""

# add your own imports here, e.g.
import numpy as np
import pandas as pd

from hdutils import (
    ComponentInputValidationException,
    parse_value,  # noqa: E402
)

# %%
# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "df_to_reindex": {"data_type": "DATAFRAME"},
        "index_column": {"data_type": "STRING", "default_value": "timestamp"},
    },
    "outputs": {
        "reindexed_df": {"data_type": "DATAFRAME"},
    },
    "name": "Set Column as Index",
    "category": "Index Operations",
    "description": "Set the specified column (default timestamp) as the index of the DataFrame.",
    "version_tag": "1.0.0",
    "id": "21ec3b5d-ffbb-4534-9f6c-e588af0a8eae",
    "revision_group_id": "6c922176-ea46-4d8b-8352-477e4d45265c",
    "state": "RELEASED",
    "released_timestamp": "2024-11-28T14:23:10.371101+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, df_to_reindex, index_column="timestamp"):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    # check whether index_column is in the columns and is appropriate as the index of a dataframe
    if not index_column in df_to_reindex.columns:
        raise ComponentInputValidationException(
            f"There is no column {index_column} in the DataFrame passed to df_to_reindex, but there should be.",
            invalid_component_inputs=["df_to_reindex", "index_column"],
        )

    if df_to_reindex[index_column].isna().any():
        raise ComponentInputValidationException(
            f"No missing values are allowed in the column {index_column} if it is to be set as the dataframe index.",
            invalid_component_inputs=["df_to_reindex"],
        )

    if df_to_reindex[index_column].duplicated().any():
        raise ComponentInputValidationException(
            f"No duplicate values are allowed in the column {index_column} if it is to be set as the dataframe index.",
            invalid_component_inputs=["df_to_reindex"],
        )

    reindexed_df = df_to_reindex.set_index(index_column)
    reindexed_df.index.name = None
    return {"reindexed_df": reindexed_df}


# Testing
try:
    import pytest
except ImportError:
    pass
else:

    @pytest.fixture()
    def timestamp_in_columns_df():
        values = [1.0, 1.2, 1.2]
        timestamps = pd.to_datetime(
            [
                "2019-08-01T15:45:36.000Z",
                "2019-08-02T11:33:41.000Z",
                "2019-08-03T11:57:41.000Z",
            ],
            format="%Y-%m-%dT%H:%M:%S.%fZ",
        ).tz_localize("UTC")

        return pd.DataFrame({"timestamp": timestamps, "value": values})

    @pytest.fixture()
    def timestamp_in_index_df():
        values = [1.0, 1.2, 1.2]
        timestamps = pd.to_datetime(
            [
                "2019-08-01T15:45:36.000Z",
                "2019-08-02T11:33:41.000Z",
                "2019-08-03T11:57:41.000Z",
            ],
            format="%Y-%m-%dT%H:%M:%S.%fZ",
        ).tz_localize("UTC")

        return pd.DataFrame({"value": values}, index=timestamps)

    def test_run_from_test_wiring():
        result = main(
            **{
                inp_wiring["workflow_input_name"]: parse_value(
                    inp_wiring["filters"]["value"],
                    COMPONENT_INFO["inputs"][inp_wiring["workflow_input_name"]]["data_type"],
                    nullable=True,
                )
                for inp_wiring in TEST_WIRING_FROM_PY_FILE_IMPORT["input_wirings"]
                if inp_wiring.get("adapter_id", "direct_provisioning") == "direct_provisioning"
            }
        )

        if not isinstance(result, dict):
            raise TypeError("The result is not a dict")

    def test_if_output_df_equals_expectation(timestamp_in_index_df, timestamp_in_columns_df):
        output_df = main(df_to_reindex=timestamp_in_columns_df)["reindexed_df"]

        pd.testing.assert_frame_equal(output_df, timestamp_in_index_df)

    def test_run_with_invalid_index_column(timestamp_in_columns_df):
        with pytest.raises(ComponentInputValidationException):
            main(df_to_reindex=timestamp_in_columns_df, index_column="not_a_valid_column")

    def test_run_with_missing_values_in_index_column(timestamp_in_columns_df):
        input_df = timestamp_in_columns_df
        input_df.loc[0, "timestamp"] = np.nan

        with pytest.raises(ComponentInputValidationException):
            main(df_to_reindex=input_df)

    def test_run_with_duplicates_in_index_column(timestamp_in_columns_df):
        input_df = timestamp_in_columns_df
        input_df.loc[0, "timestamp"] = input_df.loc[1, "timestamp"]

        with pytest.raises(ComponentInputValidationException):
            main(df_to_reindex=input_df)


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "df_to_reindex",
            "filters": {
                "value": '\n{\n    "timestamp": {\n        "0": "2019-08-01T15:45:36.000Z",\n        "1": "2019-08-02T11:33:41.000Z",\n        "2": "2019-08-03T11:57:41.000Z"\n    },\n    "value": {\n        "0": 1.0,\n        "1": 1.2,\n        "2": 1.2\n    }\n}'
            },
        },
        {
            "workflow_input_name": "index_column",
            "use_default_value": True,
            "filters": {"value": "timestamp"},
        },
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "df_to_reindex",
            "filters": {
                "value": '\n{\n    "timestamp": {\n        "0": "2019-08-01T15:45:36.000Z",\n        "1": "2019-08-02T11:33:41.000Z",\n        "2": "2019-08-03T11:57:41.000Z"\n    },\n    "value": {\n        "0": 1.0,\n        "1": 1.2,\n        "2": 1.2\n    }\n}'
            },
        },
        {
            "workflow_input_name": "index_column",
            "use_default_value": True,
            "filters": {"value": "timestamp"},
        },
    ]
}


# %%
