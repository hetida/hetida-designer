from copy import deepcopy

import numpy as np
import pandas as pd
import pytest
from hdhelpers.metadata import attach_metadata

from hdutils import add_columns_from_metric_metadata


def metric(metric_id: str, **fields: object) -> dict:
    return {
        "id": metric_id,
        "name": f"name of {metric_id}",
        "value_dimensions": [{"column": "value", "unit": "m", "measurement": None}],
    } | fields


@pytest.fixture(params=["plain", "attached"])
def base_multitsframe(request: pytest.FixtureRequest) -> pd.DataFrame:
    multitsframe = pd.DataFrame(
        {
            "metric": ["a", "b", "a", "a", "b", "c"],
            "timestamp": pd.date_range(start="2025-11-25T08:00:00+00:00", freq="1h", periods=6),
            "value": [42.1, 22.0, 42.2, 42.3, 22.1, 0.3],
        }
    )
    multitsframe.attrs = {
        "dataset_metadata": {
            "metric_key": "id",
            "queried_metrics": ["a", "b", "c"],
            "ref_interval_start_timestamp": "2025-11-25T08:00:00+00:00",
            "ref_interval_end_timestamp": "2025-11-25T13:00:00+00:00",
            "ref_interval_type": "closed",
        },
        "metrics": [
            metric("a", external_id="AA", aks="A", inherited={"site": "north"}),
            metric("b", external_id="BB", aks="B"),
            metric("c"),
        ],
    }
    if request.param == "attached":
        assert attach_metadata(multitsframe) is not None
    return multitsframe


def copy_of(multitsframe: pd.DataFrame) -> pd.DataFrame:
    copied = multitsframe.copy()
    copied.attrs = deepcopy(multitsframe.attrs)
    return copied


def test_add_columns_to_multitsframe_from_metric_metadata(base_multitsframe):
    multitsframe = add_columns_from_metric_metadata(
        copy_of(base_multitsframe), keys=["aks"], default_value="CCC"
    )
    assert multitsframe["aks"].to_numpy().tolist() == ["A", "B", "A", "A", "B", "CCC"]

    multitsframe = add_columns_from_metric_metadata(copy_of(base_multitsframe), keys=["aks"])
    assert multitsframe["aks"].to_numpy().tolist()[:5] == ["A", "B", "A", "A", "B"]
    assert np.isnan(multitsframe["aks"].iloc[5])

    # nested fields and the fallbacks of the conventions
    multitsframe = add_columns_from_metric_metadata(
        copy_of(base_multitsframe), keys=[["inherited", "site"], "unit"], default_value="CCC"
    )
    assert multitsframe["site"].to_numpy().tolist() == ["north", "CCC", "north", "north"] + [
        "CCC",
        "CCC",
    ]
    assert set(multitsframe["unit"]) == {"m"}


def test_replace_metric_col_from_metric_metadata(base_multitsframe):
    multitsframe = add_columns_from_metric_metadata(
        copy_of(base_multitsframe), replace_metric_col_with_key="external_id"
    )
    assert multitsframe["metric"].to_numpy().tolist() == ["AA", "BB", "AA", "AA", "BB", "c"]
    assert "external_id" not in multitsframe.columns

    multitsframe = add_columns_from_metric_metadata(
        copy_of(base_multitsframe), replace_metric_col_with_key=["inherited", "site"]
    )
    assert multitsframe["metric"].to_numpy().tolist() == ["north", "b", "north", "north", "b", "c"]


def test_metadata_not_following_conventions_adds_nothing():
    multitsframe = pd.DataFrame({"metric": ["a"], "timestamp": [pd.Timestamp.now()], "value": [1]})
    # the older structure
    multitsframe.attrs = {"by_metric": {"a": {"aks": "A"}}}

    result = add_columns_from_metric_metadata(multitsframe, keys=["aks"])

    assert list(result.columns) == ["metric", "timestamp", "value"]
