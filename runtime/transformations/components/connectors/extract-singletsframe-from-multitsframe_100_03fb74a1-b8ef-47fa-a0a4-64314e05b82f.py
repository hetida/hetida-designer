"""Documentation for Extract SingleTSFrame from MultiTSFrame

# Extract SingleTSFrame from MultiTSFrame

## Description
Extract the data of a single metric of a MultiTSFrame as a SingleTSFrame.

## Inputs
* **multitsframe** (MultiTSFrame): The input MultiTSFrame.
* **metric** (String): The metric to extract. Must occur in the "metric" column of the multitsframe.

## Outputs
* **singletsframe** (SingleTSFrame): The rows of the multitsframe belonging to **metric**, with the "metric" column removed.

## Details
A MULTITSFRAME holds multiple metrics, distinguished by its "metric" column. A SINGLETSFRAME holds exactly one metric and therefore has no "metric" column — the metric is identified in the metadata instead. This component selects the rows of one metric, drops the "metric" column and keeps all value dimensions (all remaining columns besides "timestamp").

The metadata (`.attrs`) is narrowed down accordingly following the [metadata conventions](https://hetida.github.io/hetida-designer/user_guide/attached_metadata/):

* `dataset_metadata.single_metric` is set to **metric**,
* the `metrics` entries are reduced to the one entry belonging to **metric** (identified via `dataset_metadata.metric_key`, defaulting to "id"),
* everything else, in particular `value_dimensions_shared`, is carried over unchanged.

Raises a ComponentInputValidationException if **metric** does not occur in the multitsframe.

## Examples
The json input of a typical call of this component is
```
{
    "multitsframe": {
        "value": [1.0, 1.2, 0.5],
        "metric": ["a", "b", "a"],
        "timestamp": [
            "2019-08-01T15:42:36.000Z",
            "2019-08-01T15:45:36.000Z",
            "2019-08-01T15:48:36.000Z"
        ]
    },
    "metric": "a"
}
```
"""

import copy

from hdutils import ComponentInputValidationException


def narrow_metadata_to_metric(attrs, metric):
    """Reduce multitsframe metadata to the metadata of a single metric

    Sets dataset_metadata.single_metric and keeps only the entry of the given metric in
    the "metrics" metadata. Also handles the simpler / older metadata structures where
    metric metadata is a dict keyed by metric.
    """
    narrowed = copy.deepcopy(attrs) if attrs else {}

    dataset_metadata = narrowed.get("dataset_metadata")
    if not isinstance(dataset_metadata, dict):
        dataset_metadata = {}
        narrowed["dataset_metadata"] = dataset_metadata
    dataset_metadata["single_metric"] = metric
    metric_key = dataset_metadata.get("metric_key") or "id"

    if isinstance(narrowed.get("metrics"), list):
        narrowed["metrics"] = [
            metric_metadata
            for metric_metadata in narrowed["metrics"]
            if isinstance(metric_metadata, dict) and metric_metadata.get(metric_key) == metric
        ]

    # simpler / older structures: mappings keyed by metric
    for key in ("metrics", "by_metric", "metric_metadata"):
        if isinstance(narrowed.get(key), dict):
            narrowed[key] = {metric: narrowed[key][metric]} if metric in narrowed[key] else {}

    return narrowed


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "multitsframe": {"data_type": "MULTITSFRAME"},
        "metric": {"data_type": "STRING"},
    },
    "outputs": {
        "singletsframe": {"data_type": "SINGLETSFRAME"},
    },
    "name": "Extract SingleTSFrame from MultiTSFrame",
    "category": "Connectors",
    "description": "Extract the data of a single metric of a MultiTSFrame as a SingleTSFrame",
    "version_tag": "1.0.0",
    "id": "03fb74a1-b8ef-47fa-a0a4-64314e05b82f",
    "revision_group_id": "6841e125-9662-4aab-a57e-a5a3f74e4077",
    "state": "RELEASED",
    "released_timestamp": "2026-08-05T10:00:00+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, multitsframe, metric):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    occurring_metrics = multitsframe["metric"].unique().tolist()
    if metric not in occurring_metrics:
        raise ComponentInputValidationException(
            f'The metric "{metric}" does not occur in the "metric" column of the provided '
            f"MultiTSFrame, which contains the metrics {occurring_metrics}.",
            invalid_component_inputs=["metric"],
        )

    singletsframe = multitsframe[multitsframe["metric"] == metric].drop(columns=["metric"])
    singletsframe = singletsframe.sort_values("timestamp").reset_index(drop=True)
    singletsframe.attrs = narrow_metadata_to_metric(multitsframe.attrs, metric)

    return {"singletsframe": singletsframe}


# Testing
try:
    import pandas as pd
    import pytest
except ImportError:
    pass
else:

    @pytest.fixture
    def multitsframe():
        multitsframe = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(
                    [
                        "2019-08-01T15:48:36.000Z",
                        "2019-08-01T15:45:36.000Z",
                        "2019-08-01T15:42:36.000Z",
                    ],
                    utc=True,
                ),
                "metric": pd.Series(["a", "b", "a"], dtype="string"),
                "value": [0.5, 1.2, 1.0],
                "state": ["ok", "ok", "suspicious"],
            }
        )
        multitsframe.attrs = {
            "dataset_metadata": {"metric_key": "external_id"},
            "metrics": [
                {"external_id": "a", "name": "Metric A"},
                {"external_id": "b", "name": "Metric B"},
            ],
            "value_dimensions_shared": [{"column": "value", "unit": "°C"}],
        }
        return multitsframe

    def test_extracts_rows_and_drops_metric_column(multitsframe):
        singletsframe = main(multitsframe=multitsframe, metric="a")["singletsframe"]

        assert list(singletsframe.columns) == [  # noqa: S101
            "timestamp",
            "value",
            "state",
        ]
        assert list(singletsframe["value"]) == [1.0, 0.5]  # noqa: S101
        assert list(singletsframe["state"]) == ["suspicious", "ok"]  # noqa: S101

    def test_narrows_metadata(multitsframe):
        singletsframe = main(multitsframe=multitsframe, metric="a")["singletsframe"]

        assert singletsframe.attrs["dataset_metadata"]["single_metric"] == "a"  # noqa: S101
        assert singletsframe.attrs["dataset_metadata"]["metric_key"] == "external_id"  # noqa: S101
        assert singletsframe.attrs["metrics"] == [{"external_id": "a", "name": "Metric A"}]  # noqa: S101
        assert singletsframe.attrs["value_dimensions_shared"] == [  # noqa: S101
            {"column": "value", "unit": "°C"}
        ]
        # input attrs must not be modified
        assert len(multitsframe.attrs["metrics"]) == 2  # noqa: S101

    def test_works_without_metadata(multitsframe):
        multitsframe.attrs = {}

        singletsframe = main(multitsframe=multitsframe, metric="b")["singletsframe"]

        assert singletsframe.attrs["dataset_metadata"]["single_metric"] == "b"  # noqa: S101
        assert list(singletsframe["value"]) == [1.2]  # noqa: S101

    def test_unknown_metric_raises(multitsframe):
        with pytest.raises(ComponentInputValidationException):
            main(multitsframe=multitsframe, metric="not_present")


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "multitsframe",
            "filters": {
                "value": '{\n    "value": [\n        1,\n        1.2,\n        0.5\n    ],\n    "metric": [\n        "a",\n        "b",\n        "a"\n    ],\n    "timestamp": [\n        "2019-08-01T15:42:36.000Z",\n        "2019-08-01T15:45:36.000Z",\n        "2019-08-01T15:48:36.000Z"\n    ]\n}'
            },
        },
        {"workflow_input_name": "metric", "filters": {"value": "a"}},
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "multitsframe",
            "filters": {
                "value": '{\n    "value": [\n        1,\n        1.2,\n        0.5\n    ],\n    "metric": [\n        "a",\n        "b",\n        "a"\n    ],\n    "timestamp": [\n        "2019-08-01T15:42:36.000Z",\n        "2019-08-01T15:45:36.000Z",\n        "2019-08-01T15:48:36.000Z"\n    ]\n}'
            },
        },
        {"workflow_input_name": "metric", "filters": {"value": "a"}},
    ]
}
