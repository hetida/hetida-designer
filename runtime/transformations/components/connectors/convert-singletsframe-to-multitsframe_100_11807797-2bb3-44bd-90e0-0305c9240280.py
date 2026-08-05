"""Documentation for Convert SingleTSFrame to MultiTSFrame

# Convert SingleTSFrame to MultiTSFrame

## Description
Convert a SingleTSFrame into a MultiTSFrame with a single metric.

## Inputs
* **singletsframe** (SingleTSFrame): The input SingleTSFrame.
* **metric** (String, optional): The metric name to use. If not provided, `dataset_metadata.single_metric` from the metadata of the singletsframe is used. Default: null.

## Outputs
* **multitsframe** (MultiTSFrame): The output MultiTSFrame with exactly one metric.

## Details
A SINGLETSFRAME holds exactly one metric and therefore has no "metric" column — the metric is identified in the metadata. This component adds the "metric" column required for a MULTITSFRAME, filled with the single metric name, and keeps all value dimensions.

Use this component to feed a SingleTSFrame into components or sinks that expect a MultiTSFrame.

Raises a ComponentInputValidationException if no metric name is provided and none can be determined from the metadata, or if the singletsframe already has a column named "metric".

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
    "metric": "a"
}
```
"""

import copy

from hdutils import ComponentInputValidationException

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "singletsframe": {"data_type": "SINGLETSFRAME"},
        "metric": {"data_type": "STRING", "default_value": None},
    },
    "outputs": {
        "multitsframe": {"data_type": "MULTITSFRAME"},
    },
    "name": "Convert SingleTSFrame to MultiTSFrame",
    "category": "Connectors",
    "description": "Convert a SingleTSFrame into a MultiTSFrame with a single metric",
    "version_tag": "1.0.0",
    "id": "11807797-2bb3-44bd-90e0-0305c9240280",
    "revision_group_id": "a01e4664-057e-415e-a833-57723df33b4f",
    "state": "RELEASED",
    "released_timestamp": "2026-08-05T10:00:00+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, singletsframe, metric=None):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    if "metric" in singletsframe.columns:
        raise ComponentInputValidationException(
            'The provided SingleTSFrame already has a column named "metric". A SingleTSFrame'
            ' may use "metric" as an ordinary value column, but then it cannot be converted'
            " into a MultiTSFrame without losing that value dimension.",
            invalid_component_inputs=["singletsframe"],
        )

    attrs = copy.deepcopy(singletsframe.attrs) if singletsframe.attrs else {}

    metric_name = metric
    if metric_name in (None, ""):
        dataset_metadata = attrs.get("dataset_metadata")
        if isinstance(dataset_metadata, dict):
            metric_name = dataset_metadata.get("single_metric")

    if metric_name in (None, ""):
        raise ComponentInputValidationException(
            "No metric name provided and none could be determined from"
            ' "dataset_metadata.single_metric" in the metadata of the SingleTSFrame.',
            invalid_component_inputs=["metric"],
        )

    multitsframe = singletsframe.copy()
    multitsframe.insert(1, "metric", str(metric_name))
    multitsframe["metric"] = multitsframe["metric"].astype("string")
    multitsframe = multitsframe.sort_values("timestamp").reset_index(drop=True)
    multitsframe.attrs = attrs

    return {"multitsframe": multitsframe}


# Testing
try:
    import pandas as pd
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

    def test_metric_from_metadata(singletsframe):
        multitsframe = main(singletsframe=singletsframe)["multitsframe"]

        assert list(multitsframe.columns) == [  # noqa: S101
            "timestamp",
            "metric",
            "value",
            "state",
        ]
        assert list(multitsframe["metric"]) == ["abc.temp", "abc.temp"]  # noqa: S101
        assert list(multitsframe["value"]) == [1.0, 1.2]  # noqa: S101

    def test_explicit_metric_wins(singletsframe):
        multitsframe = main(singletsframe=singletsframe, metric="other")["multitsframe"]

        assert list(multitsframe["metric"]) == ["other", "other"]  # noqa: S101

    def test_missing_metric_raises(singletsframe):
        singletsframe.attrs = {}

        with pytest.raises(ComponentInputValidationException):
            main(singletsframe=singletsframe)

    def test_existing_metric_column_raises(singletsframe):
        singletsframe = singletsframe.rename(columns={"state": "metric"})

        with pytest.raises(ComponentInputValidationException):
            main(singletsframe=singletsframe, metric="a")


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "singletsframe",
            "filters": {
                "value": '{\n    "value": [\n        1,\n        1.2,\n        0.5\n    ],\n    "timestamp": [\n        "2019-08-01T15:42:36.000Z",\n        "2019-08-01T15:45:36.000Z",\n        "2019-08-01T15:48:36.000Z"\n    ]\n}'
            },
        },
        {"workflow_input_name": "metric", "filters": {"value": "a"}},
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
        {"workflow_input_name": "metric", "filters": {"value": "a"}},
    ]
}
