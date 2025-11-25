import numpy as np
import pandas as pd

from hdutils import add_columns_from_metric_metadata


def test_add_columns_to_multitsframe_from_metric_metadata():
    base_multitsframe = pd.DataFrame(
        {
            "metric": ["a", "b", "a", "a", "b", "c"],
            "timestamp": pd.date_range(start="2025-11-25T08:00:00+00:00", freq="1h", periods=6),
            "value": [42.1, 22.0, 42.2, 42.3, 22.1, 0.3],
        }
    )

    base_multitsframe.attrs = {
        "dataset_metadata": {},
        "by_metric": {
            "a": {"aks": "A"},
            "b": {"aks": "B"},
        },
    }

    multitsframe = base_multitsframe.copy()
    multitsframe = add_columns_from_metric_metadata(multitsframe, keys=["aks"], default_value="CCC")
    assert "aks" in multitsframe.columns
    assert multitsframe["aks"].to_numpy().tolist() == ["A", "B", "A", "A", "B", "CCC"]

    multitsframe = base_multitsframe.copy()
    multitsframe = add_columns_from_metric_metadata(multitsframe, keys=["aks"])
    assert "aks" in multitsframe.columns
    assert multitsframe["aks"].to_numpy().tolist() == ["A", "B", "A", "A", "B", np.nan]

    multitsframe = base_multitsframe.copy()
    multitsframe = add_columns_from_metric_metadata(multitsframe, replace_metric_col_with_key="aks")
    assert multitsframe["metric"].to_numpy().tolist() == ["A", "B", "A", "A", "B", "c"]
    assert "aks" not in multitsframe.columns
