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

If the metadata follows the [metadata conventions](https://hetida.github.io/hetida-designer/user_guide/attached_metadata/), it is converted into the metadata of a MultiTSFrame of the single metric. If **metric** differs from the id of the metric, it becomes its id in the field "metric", which then becomes the metric key. The field which identified the metric before, e.g. its `id` or `external_id`, is kept. Other metadata is carried over unchanged.

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

from hdhelpers.metadata import read_metadata, set_metadata

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
    meta = read_metadata(singletsframe, "SINGLETSFRAME")

    metric_name = metric
    if metric_name in (None, "") and meta is not None:
        metric_name = meta.dataset_metadata.single_metric
    elif metric_name in (None, ""):
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
    if meta is not None:
        set_metadata(multitsframe, meta.as_multitsframe(str(metric_name)))

    return {"multitsframe": multitsframe}


# Testing
try:
    import pandas as pd
    import pytest
except ImportError:
    pass
else:
    from hdhelpers.metadata import META_KEY, attrs_to_json, check_metadata_conventions

    SINGLETSFRAME_METADATA = {
        "dataset_metadata": {
            "metric_key": "id",
            "single_metric": "abc.temp",
            "queried_metrics": ["abc.temp"],
            "ref_interval_start_timestamp": "2019-08-01T15:00:00Z",
            "ref_interval_end_timestamp": "2019-08-01T16:00:00Z",
            "ref_interval_type": "closed",
        },
        "metrics": [
            {
                "id": "abc.temp",
                "name": "Temperature",
                "value_dimensions": [
                    {"column": "value", "unit": "°C", "measurement": "temperature"},
                    {"column": "state", "unit": None, "measurement": None},
                ],
            }
        ],
    }

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

    @pytest.mark.parametrize(
        ("metric", "metric_key", "metric_ids"),
        [
            (None, "id", ["abc.temp"]),
            ("abc.temp", "id", ["abc.temp"]),
            # another metric becomes the id in the field "metric"
            ("other", "metric", ["other"]),
        ],
    )
    def test_metadata_following_conventions_is_converted(
        singletsframe, metric, metric_key, metric_ids
    ):
        singletsframe.attrs = copy.deepcopy(SINGLETSFRAME_METADATA)

        multitsframe = main(singletsframe=singletsframe, metric=metric)["multitsframe"]

        assert set(multitsframe.attrs) == {META_KEY}  # noqa: S101
        assert check_metadata_conventions(multitsframe) == []  # noqa: S101
        attrs = attrs_to_json(multitsframe.attrs)
        assert attrs["dataset_metadata"]["metric_key"] == metric_key  # noqa: S101
        assert attrs["dataset_metadata"]["queried_metrics"] == metric_ids  # noqa: S101
        assert attrs["metrics"][0]["id"] == "abc.temp"  # noqa: S101
        assert len(attrs["metrics"][0]["value_dimensions"]) == 2  # noqa: S101
        # input attrs must not be modified
        assert singletsframe.attrs == SINGLETSFRAME_METADATA  # noqa: S101

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
