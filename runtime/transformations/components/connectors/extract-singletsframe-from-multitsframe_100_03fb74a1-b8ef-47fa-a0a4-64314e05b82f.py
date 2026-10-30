"""Documentation for Extract SingleTSFrame from MultiTSFrame

# Extract SingleTSFrame from MultiTSFrame

## Description
Extract the data of a single metric of a MultiTSFrame as a SingleTSFrame.

## Inputs
* **multitsframe** (MultiTSFrame): The input MultiTSFrame.
* **metric** (String): The metric to extract. Must occur in the "metric" column of the multitsframe or be known from its metadata, i.e. be listed in `dataset_metadata.queried_metrics` or have an entry under `metrics`.

## Outputs
* **singletsframe** (SingleTSFrame): The rows of the multitsframe belonging to **metric**, with the "metric" column removed. Empty if **metric** is only known from the metadata, e.g. a queried metric without data in the queried interval.

## Details
A MULTITSFRAME holds multiple metrics, distinguished by its "metric" column. A SINGLETSFRAME holds exactly one metric and therefore has no "metric" column — the metric is identified in the metadata instead. This component selects the rows of one metric, drops the "metric" column and keeps all value dimensions (all remaining columns besides "timestamp").

The metadata (`.attrs`) is narrowed down accordingly following the [metadata conventions](https://hetida.github.io/hetida-designer/user_guide/attached_metadata/):

* `dataset_metadata.single_metric` is set to **metric**,
* the `metrics` entries are reduced to the one entry belonging to **metric** (identified via `dataset_metadata.metric_key`, defaulting to "id"),
* everything else, in particular `value_dimensions_shared`, is carried over unchanged.

If the metadata follows the metadata conventions and describes **metric**, `queried_metrics` becomes **metric**, too, and the metadata is attached to the result as model (see `read_metadata` of `hdhelpers.metadata`).

Following the metadata conventions, a queried metric may have no data, e.g. in the queried interval. For a metric which does not occur in the "metric" column, but is listed in `dataset_metadata.queried_metrics` or has an entry under `metrics` (identified via `dataset_metadata.metric_key`), the result is an empty SINGLETSFRAME with the columns of the multitsframe besides "metric" and the metadata narrowed down as described.

Raises a ComponentInputValidationException if **metric** neither occurs in the multitsframe nor is known from its metadata in this way.

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

import pandas as pd
from hdhelpers.metadata import attrs_to_json, read_metadata, set_metadata

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


def metric_known_from_metadata(meta, attrs, metric):
    """Whether the metadata lists the metric as queried or describes it under metrics

    meta is the metadata following the conventions, None otherwise. Then the metric is looked
    up in attrs, under "metrics" via the field named by dataset_metadata.metric_key (defaulting
    to "id"). Such a metric may have no data, e.g. in the queried interval.
    """
    if meta is not None:
        return metric in meta.dataset_metadata.queried_metrics or metric in meta.metric_ids()

    dataset_metadata = attrs.get("dataset_metadata")
    if not isinstance(dataset_metadata, dict):
        dataset_metadata = {}
    queried_metrics = dataset_metadata.get("queried_metrics")
    if isinstance(queried_metrics, list) and metric in queried_metrics:
        return True
    metric_key = dataset_metadata.get("metric_key") or "id"
    metrics = attrs.get("metrics")
    return isinstance(metrics, list) and any(
        isinstance(metric_metadata, dict) and metric_metadata.get(metric_key) == metric
        for metric_metadata in metrics
    )


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
    meta = read_metadata(multitsframe, "MULTITSFRAME")
    occurring_metrics = multitsframe["metric"].unique().tolist()
    if metric not in occurring_metrics and not metric_known_from_metadata(
        meta, attrs_to_json(multitsframe.attrs) if meta is None else {}, metric
    ):
        raise ComponentInputValidationException(
            f'The metric "{metric}" does not occur in the "metric" column of the provided '
            f"MultiTSFrame, which contains the metrics {occurring_metrics}, nor in its metadata"
            " as queried metric or under metrics.",
            invalid_component_inputs=["metric"],
        )

    singletsframe = multitsframe[multitsframe["metric"] == metric].drop(columns=["metric"])
    if not isinstance(singletsframe["timestamp"].dtype, pd.DatetimeTZDtype):
        # e.g. the timestamp column of a MultiTSFrame without any rows
        singletsframe["timestamp"] = pd.to_datetime(singletsframe["timestamp"], utc=True)
    singletsframe = singletsframe.sort_values("timestamp").reset_index(drop=True)
    if meta is not None and metric in meta.metric_ids():
        set_metadata(singletsframe, meta.narrowed_to(metric))
    else:
        singletsframe.attrs = narrow_metadata_to_metric(attrs_to_json(multitsframe.attrs), metric)

    return {"singletsframe": singletsframe}


# Testing
try:
    import pandas as pd
    import pytest
except ImportError:
    pass
else:
    from hdhelpers.metadata import META_KEY, attach_metadata, check_metadata_conventions

    MULTITSFRAME_METADATA = {
        "dataset_metadata": {
            "metric_key": "external_id",
            "queried_metrics": ["a", "b"],
            "ref_interval_start_timestamp": "2019-08-01T15:00:00Z",
            "ref_interval_end_timestamp": "2019-08-01T16:00:00Z",
            "ref_interval_type": "closed",
        },
        "metrics": [
            {
                "id": f"id of {metric}",
                "external_id": metric,
                "name": f"Metric {metric}",
                "value_dimensions": [
                    {"column": "value", "unit": "°C", "measurement": "temperature"},
                    {"column": "state", "unit": None, "measurement": None},
                ],
            }
            for metric in ("a", "b")
        ],
        "value_dimensions_shared": [{"column": "value", "description": "Measured"}],
    }

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

    @pytest.mark.parametrize("attached", [False, True])
    def test_metadata_following_conventions_is_narrowed(multitsframe, attached):
        multitsframe.attrs = copy.deepcopy(MULTITSFRAME_METADATA)
        if attached:
            attach_metadata(multitsframe)

        singletsframe = main(multitsframe=multitsframe, metric="a")["singletsframe"]

        assert set(singletsframe.attrs) == {META_KEY}  # noqa: S101
        assert check_metadata_conventions(singletsframe) == []  # noqa: S101
        meta = read_metadata(singletsframe, "SINGLETSFRAME", required=True)
        assert meta.dataset_metadata.queried_metrics == ("a",)  # noqa: S101
        assert meta.metric().name == "Metric a"  # noqa: S101
        assert meta.value_dimensions_shared[0].description == "Measured"  # noqa: S101

    def test_works_without_metadata(multitsframe):
        multitsframe.attrs = {}

        singletsframe = main(multitsframe=multitsframe, metric="b")["singletsframe"]

        assert singletsframe.attrs["dataset_metadata"]["single_metric"] == "b"  # noqa: S101
        assert list(singletsframe["value"]) == [1.2]  # noqa: S101

    def test_unknown_metric_raises(multitsframe):
        with pytest.raises(ComponentInputValidationException):
            main(multitsframe=multitsframe, metric="not_present")

    @pytest.mark.parametrize("attached", [False, True])
    def test_metric_without_data_known_from_metadata(multitsframe, attached):
        attrs = copy.deepcopy(MULTITSFRAME_METADATA)
        attrs["dataset_metadata"]["queried_metrics"].append("c")
        attrs["metrics"].append(attrs["metrics"][0] | {"id": "id of c", "external_id": "c"})
        multitsframe.attrs = attrs
        if attached:
            attach_metadata(multitsframe)

        singletsframe = main(multitsframe=multitsframe, metric="c")["singletsframe"]

        assert len(singletsframe) == 0  # noqa: S101
        assert list(singletsframe.columns) == ["timestamp", "value", "state"]  # noqa: S101
        assert isinstance(singletsframe["timestamp"].dtype, pd.DatetimeTZDtype)  # noqa: S101
        assert check_metadata_conventions(singletsframe) == []  # noqa: S101
        meta = read_metadata(singletsframe, "SINGLETSFRAME", required=True)
        assert meta.dataset_metadata.single_metric == "c"  # noqa: S101

    @pytest.mark.parametrize(
        "attrs",
        [
            # only listed as queried metric, without metric metadata
            {"dataset_metadata": {"metric_key": "external_id", "queried_metrics": ["a", "c"]}},
            # only described under metrics, in metadata not following the conventions
            {"dataset_metadata": {"metric_key": "external_id"}, "metrics": [{"external_id": "c"}]},
        ],
    )
    def test_metric_without_data_known_from_other_metadata(multitsframe, attrs):
        multitsframe.attrs = attrs

        singletsframe = main(multitsframe=multitsframe, metric="c")["singletsframe"]

        assert len(singletsframe) == 0  # noqa: S101
        assert singletsframe.attrs["dataset_metadata"]["single_metric"] == "c"  # noqa: S101

    def test_empty_multitsframe_with_queried_metric():
        multitsframe = pd.DataFrame({"timestamp": [], "metric": [], "value": []})
        multitsframe.attrs = {"dataset_metadata": {"queried_metrics": ["a"]}}

        singletsframe = main(multitsframe=multitsframe, metric="a")["singletsframe"]

        assert list(singletsframe.columns) == ["timestamp", "value"]  # noqa: S101
        assert isinstance(singletsframe["timestamp"].dtype, pd.DatetimeTZDtype)  # noqa: S101


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
