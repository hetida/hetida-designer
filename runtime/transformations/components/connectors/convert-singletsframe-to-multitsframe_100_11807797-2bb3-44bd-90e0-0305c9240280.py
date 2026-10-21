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

The metadata (`.attrs`) is carried over. If it contains dataset metadata, its `single_metric` and `queried_metrics` are set to the metric name, as well as the field identifying the metric (`dataset_metadata.metric_key`, defaulting to "id") in the single entry under `metrics`. So metadata following the [metadata conventions](https://hetida.github.io/hetida-designer/user_guide/attached_metadata/) for a SINGLETSFRAME follows them for the resulting MULTITSFRAME, too, also if another metric name is provided.

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


def set_metric_in_metadata(attrs, metric_name):
    """Identify the single metric of metadata following the metadata conventions by metric_name

    Sets single_metric, queried_metrics and the metric_key field of the single entry under
    metrics. Changes attrs in place. Metadata without dataset metadata stays unchanged.
    """
    dataset_metadata = attrs.get("dataset_metadata")
    if not isinstance(dataset_metadata, dict):
        return
    dataset_metadata["single_metric"] = metric_name
    dataset_metadata["queried_metrics"] = [metric_name]
    metrics = attrs.get("metrics")
    if isinstance(metrics, list) and len(metrics) == 1 and isinstance(metrics[0], dict):
        metrics[0][dataset_metadata.get("metric_key") or "id"] = metric_name


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

    set_metric_in_metadata(attrs, str(metric_name))

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
    from hetdesrun.models.metadata_conventions import check_metadata_conventions

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

    @pytest.fixture
    def singletsframe_metadata():
        # following the metadata conventions for a SINGLETSFRAME
        return {
            "dataset_metadata": {
                "metric_key": "external_id",
                "single_metric": "abc.temp",
                "queried_metrics": ["abc.temp"],
                "ref_interval_start_timestamp": "2019-08-01T15:00:00Z",
                "ref_interval_end_timestamp": "2019-08-01T16:00:00Z",
                "ref_interval_type": "closed",
            },
            "metrics": [
                {
                    "id": "7ab8c419",
                    "external_id": "abc.temp",
                    "name": "Temperature",
                    "value_dimensions": [
                        {"column": "value", "unit": "°C", "measurement": "temperature"},
                        {"column": "state", "unit": None, "measurement": None},
                    ],
                }
            ],
        }

    @pytest.mark.parametrize("metric", [None, "abc.temp", "other"])
    def test_metadata_follows_conventions(singletsframe, singletsframe_metadata, metric):
        singletsframe.attrs = singletsframe_metadata
        assert check_metadata_conventions(singletsframe, "SINGLETSFRAME") == []  # noqa: S101

        multitsframe = main(singletsframe=singletsframe, metric=metric)["multitsframe"]

        assert check_metadata_conventions(multitsframe) == []  # noqa: S101
        metric_name = metric or "abc.temp"
        assert multitsframe.attrs["metrics"][0]["external_id"] == metric_name  # noqa: S101
        assert multitsframe.attrs["metrics"][0]["id"] == "7ab8c419"  # noqa: S101
        assert multitsframe.attrs["dataset_metadata"]["queried_metrics"] == [  # noqa: S101
            metric_name
        ]
        # input attrs must not be modified
        assert singletsframe.attrs == singletsframe_metadata  # noqa: S101

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
