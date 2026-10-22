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
* `dataset_metadata.queried_metrics` is reduced to **metric**,
* the `metrics` entries are reduced to the one entry belonging to **metric** (identified via `dataset_metadata.metric_key`, defaulting to "id"),
* everything else, in particular `value_dimensions_shared`, is carried over unchanged.

So metadata following the conventions for a MULTITSFRAME follows them for the resulting SINGLETSFRAME, too.

Following the metadata conventions, a queried metric may have no data, e.g. in the queried interval. For a metric which does not occur in the "metric" column, but is listed in `dataset_metadata.queried_metrics` or has an entry under `metrics` (identified via `dataset_metadata.metric_key`), the result is an empty SINGLETSFRAME with the columns of the multitsframe besides "metric" and the metadata narrowed down as described above.

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

from hdutils import ComponentInputValidationException


def narrow_metadata_to_metric(attrs, metric):
    """Reduce multitsframe metadata to the metadata of a single metric

    Sets dataset_metadata.single_metric, reduces dataset_metadata.queried_metrics to the given
    metric and keeps only the entry of the given metric in the "metrics" metadata. Also handles
    the simpler / older metadata structures where metric metadata is a dict keyed by metric.
    """
    # narrowed on a shallow copy, replacing the changed containers, and only copied deeply at the
    # end, so that the metadata of the other metrics is not copied
    narrowed = dict(attrs) if attrs else {}

    dataset_metadata = narrowed.get("dataset_metadata")
    dataset_metadata = dict(dataset_metadata) if isinstance(dataset_metadata, dict) else {}
    narrowed["dataset_metadata"] = dataset_metadata
    dataset_metadata["single_metric"] = metric
    if isinstance(dataset_metadata.get("queried_metrics"), list):
        dataset_metadata["queried_metrics"] = [metric]
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

    return copy.deepcopy(narrowed)


def metric_known_from_metadata(attrs, metric):
    """Whether metadata following the conventions lists the metric as queried or describes it

    The metric is known if it occurs in dataset_metadata.queried_metrics or if an entry under
    "metrics" has it as value of the field named by dataset_metadata.metric_key (defaulting to
    "id"). Such a metric may have no data, e.g. in the queried interval.
    """
    if not isinstance(attrs, dict):
        return False
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
    # Without the metadata, since pandas copies it on every operation below. Under copy-on-write
    # this neither copies the data nor changes the input.
    data = pd.DataFrame(multitsframe)
    data.attrs = {}

    occurring_metrics = data["metric"].unique().tolist()
    if metric not in occurring_metrics and not metric_known_from_metadata(
        multitsframe.attrs, metric
    ):
        raise ComponentInputValidationException(
            f'The metric "{metric}" does not occur in the "metric" column of the provided '
            f"MultiTSFrame, which contains the metrics {occurring_metrics}, nor in its metadata"
            " as queried metric or under metrics.",
            invalid_component_inputs=["metric"],
        )

    singletsframe = data[data["metric"] == metric].drop(columns=["metric"])
    if not isinstance(singletsframe["timestamp"].dtype, pd.DatetimeTZDtype):
        # e.g. the timestamp column of a MultiTSFrame without any rows
        singletsframe["timestamp"] = pd.to_datetime(singletsframe["timestamp"], utc=True)
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
    from hdutils import validate_singlets_properties
    from hetdesrun.models.metadata_conventions import check_metadata_conventions

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

    def test_input_is_not_changed_and_metadata_is_copied(multitsframe):
        expected_attrs = copy.deepcopy(multitsframe.attrs)
        expected_input = multitsframe.copy()

        singletsframe = main(multitsframe=multitsframe, metric="a")["singletsframe"]
        singletsframe.attrs["dataset_metadata"]["metric_key"] = "changed"
        singletsframe.attrs["metrics"][0]["name"] = "changed"
        singletsframe.attrs["value_dimensions_shared"][0]["unit"] = "K"

        assert multitsframe.attrs == expected_attrs  # noqa: S101
        pd.testing.assert_frame_equal(multitsframe, expected_input)

    def test_metadata_follows_conventions(multitsframe):
        multitsframe.attrs = {
            "dataset_metadata": {
                "metric_key": "external_id",
                "queried_metrics": ["a", "b", "c"],
                "ref_interval_start_timestamp": "2019-08-01T15:00:00Z",
                "ref_interval_end_timestamp": "2019-08-01T16:00:00Z",
                "ref_interval_type": "closed",
            },
            "metrics": [
                {
                    "external_id": metric,
                    "id": f"id of {metric}",
                    "name": f"Metric {metric}",
                    "value_dimensions": [
                        {"column": "value", "unit": "°C", "measurement": "temperature"},
                        {"column": "state", "unit": None, "measurement": None},
                    ],
                }
                for metric in ["a", "b", "c"]
            ],
        }
        assert check_metadata_conventions(multitsframe) == []  # noqa: S101

        singletsframe = main(multitsframe=multitsframe, metric="b")["singletsframe"]

        assert check_metadata_conventions(singletsframe, "SINGLETSFRAME") == []  # noqa: S101
        assert singletsframe.attrs["dataset_metadata"]["queried_metrics"] == ["b"]  # noqa: S101
        assert [metric["id"] for metric in singletsframe.attrs["metrics"]] == [  # noqa: S101
            "id of b"
        ]

    def test_works_without_metadata(multitsframe):
        multitsframe.attrs = {}

        singletsframe = main(multitsframe=multitsframe, metric="b")["singletsframe"]

        assert singletsframe.attrs["dataset_metadata"]["single_metric"] == "b"  # noqa: S101
        assert list(singletsframe["value"]) == [1.2]  # noqa: S101

    def test_unknown_metric_raises(multitsframe):
        with pytest.raises(ComponentInputValidationException):
            main(multitsframe=multitsframe, metric="not_present")

    def metadata_following_conventions(queried_metrics, described_metrics):
        return {
            "dataset_metadata": {
                "metric_key": "external_id",
                "queried_metrics": queried_metrics,
                "ref_interval_start_timestamp": "2019-08-01T15:00:00Z",
                "ref_interval_end_timestamp": "2019-08-01T16:00:00Z",
                "ref_interval_type": "closed",
                "default_timezone": "Europe/Berlin",
            },
            "metrics": [
                {
                    "external_id": metric,
                    "id": f"id of {metric}",
                    "name": f"Metric {metric}",
                    "value_dimensions": [
                        {"column": "value", "unit": "°C", "measurement": "temperature"},
                        {"column": "state", "unit": None, "measurement": None},
                    ],
                }
                for metric in described_metrics
            ],
        }

    def test_queried_metric_without_data_gives_empty_singletsframe(multitsframe):
        multitsframe.attrs = metadata_following_conventions(["a", "b", "c"], ["a", "b", "c"])

        singletsframe = main(multitsframe=multitsframe, metric="c")["singletsframe"]

        assert len(singletsframe) == 0  # noqa: S101
        assert list(singletsframe.columns) == ["timestamp", "value", "state"]  # noqa: S101
        assert singletsframe["value"].dtype == multitsframe["value"].dtype  # noqa: S101
        assert singletsframe["state"].dtype == multitsframe["state"].dtype  # noqa: S101
        validate_singlets_properties(singletsframe.copy())
        expected_attrs = metadata_following_conventions(["c"], ["c"])
        expected_attrs["dataset_metadata"]["single_metric"] = "c"
        assert singletsframe.attrs == expected_attrs  # noqa: S101
        assert check_metadata_conventions(singletsframe, "SINGLETSFRAME") == []  # noqa: S101

    @pytest.mark.parametrize(
        ("queried_metrics", "described_metrics"),
        [
            pytest.param(["a", "b", "c"], ["a", "b"], id="only queried"),
            pytest.param(["a", "b"], ["a", "b", "c"], id="only described under metrics"),
        ],
    )
    def test_metric_known_from_metadata_without_data(
        multitsframe, queried_metrics, described_metrics
    ):
        multitsframe.attrs = metadata_following_conventions(queried_metrics, described_metrics)

        singletsframe = main(multitsframe=multitsframe, metric="c")["singletsframe"]

        assert len(singletsframe) == 0  # noqa: S101
        assert singletsframe.attrs["dataset_metadata"]["single_metric"] == "c"  # noqa: S101

    def test_empty_multitsframe_gives_empty_singletsframe():
        multitsframe = pd.DataFrame({"timestamp": [], "metric": [], "value": []})
        multitsframe.attrs = metadata_following_conventions(["c"], ["c"])

        singletsframe = main(multitsframe=multitsframe, metric="c")["singletsframe"]

        assert list(singletsframe.columns) == ["timestamp", "value"]  # noqa: S101
        assert isinstance(singletsframe["timestamp"].dtype, pd.DatetimeTZDtype)  # noqa: S101
        assert str(singletsframe["timestamp"].dt.tz) == "UTC"  # noqa: S101
        validate_singlets_properties(singletsframe.copy())

    @pytest.mark.parametrize(
        "attrs",
        [
            pytest.param(
                metadata_following_conventions(["a", "b", "c"], ["a", "b", "c"]),
                id="metadata following the conventions",
            ),
            pytest.param(
                {"ref_metrics": ["a", "b", "d"], "by_metric": {"d": {"unit": "°C"}}},
                id="older metadata structure",
            ),
            pytest.param(
                {"metrics": {"d": {"unit": "°C"}}}, id="metrics as mapping (older convention)"
            ),
        ],
    )
    def test_metric_neither_in_data_nor_in_metadata_raises(multitsframe, attrs):
        multitsframe.attrs = attrs

        with pytest.raises(ComponentInputValidationException, match='"d"'):
            main(multitsframe=multitsframe, metric="d")


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
