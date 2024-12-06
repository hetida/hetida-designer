"""Documentation for Index to Column

# Reset Index and Save as Column
## Description
Uses the pandas reset_index method to reset the index of a DataFrame and save the previous index as a new column.

## Inputs
* **df** (Pandas DataFrame): The input DataFrame the index of which will be reset.
* **index_name** (String): The name of the column that the previous index will be saved as. Default: "timestamp".

## Outputs
* **df_with_reset_index** (Pandas DataFrame): The output DataFrame with the reset index and the previous index index saved as a column.

## Details
Resets the index of the df and saves it as a new column with the name index_name.

The index_name is expected not to occur in the columns of the df. If it does, a ComponentInputValidationException is raised.

"""

# add your own imports here, e.g.
import pandas as pd

from hdutils import (
    ComponentInputValidationException,
    parse_value,  # noqa: E402
)

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "df": {"data_type": "DATAFRAME"},
        "index_name": {"data_type": "STRING", "default_value": "timestamp"},
    },
    "outputs": {
        "df_with_reset_index": {"data_type": "DATAFRAME"},
    },
    "name": "Index to Column",
    "category": "Index Operations",
    "description": "Uses the pandas reset_index method to reset the index of a DataFrame and save the previous index as a column.",  # noqa: E501
    "version_tag": "1.0.1",
    "id": "0f24fedc-a38f-4123-a487-989d7a8037d7",
    "revision_group_id": "175f432d-0efd-499c-bf62-85aa42761de9",
    "state": "RELEASED",
    "released_timestamp": "2024-12-06T08:47:44.686957+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, df, index_name="timestamp"):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    # check whether index_column is in the columns and is appropriate as the index of a dataframe
    if index_name in df.columns:
        raise ComponentInputValidationException(
            f"There is already a column named {index_name} in the DataFrame passed to df.",
            invalid_component_inputs=["df", "index_name"],
        )

    reset_df = df.reset_index(drop=False, names=index_name, allow_duplicates=False)
    return {"df_with_reset_index": reset_df}


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

        assert isinstance(result, dict)  # noqa: S101

    def test_if_output_df_equals_expectation(timestamp_in_index_df, timestamp_in_columns_df):
        output_df = main(df=timestamp_in_index_df)["df_with_reset_index"]

        pd.testing.assert_frame_equal(output_df, timestamp_in_columns_df)

    def test_run_with_invalid_index_column(timestamp_in_index_df):
        with pytest.raises(
            ComponentInputValidationException, match="There is already a column named*"
        ):
            main(df=timestamp_in_index_df, index_name="value")


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "df",
            "filters": {
                "value": '{\n    "value": {\n        "2019-08-01T15:45:36.000Z": 1.0,\n        "2019-08-02T11:33:41.000Z": 1.2,\n       "2019-08-03T11:57:41.000Z": 1.2\n    }\n}'
            },
        },
        {
            "workflow_input_name": "index_name",
            "use_default_value": True,
            "filters": {"value": "timestamp"},
        },
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "df_to_reset_index",
            "filters": {
                "value": '{\n    "value": {\n        "2019-08-01T15:45:36.000Z": 1.0,\n        "2019-08-02T11:33:41.000Z": 1.2,\n       "2019-08-03T11:57:41.000Z": 1.2\n    }\n}'
            },
        },
        {
            "workflow_input_name": "index_name",
            "use_default_value": True,
            "filters": {"value": "timestamp"},
        },
    ]
}
