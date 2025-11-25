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

    base_multitsframe.attrs = {
        "dataset_metadata": {},
        "by_metric": {
            "a": {
                "structured_metadata": {
                    "metric": {  # metadata associated to the current metric. These are
                        "name": "AAAAA",
                        "display_name": "some A",
                        "short_display_name": "a",
                        "description": "some descriptions",
                        "external_id": "AA",
                        "channel_id": "abc123-...",
                    }
                }
            },
            "b": {
                "structured_metadata": {
                    "metric": {  # metadata associated to the current metric. These are
                        "name": "BBBBB",
                        "display_name": "some B",
                        "short_display_name": "b",
                        "description": "some descriptions",
                        "external_id": "BB",
                        "channel_id": "abc123-...",
                    }
                }
            },
        },
    }
    multitsframe = base_multitsframe.copy()
    multitsframe = add_columns_from_metric_metadata(
        multitsframe,
        keys=[
            ["structured_metadata", "metric", "external_id"],
            ["structured_metadata", "metric", "channel_id"],
        ],
        default_value="CCC",
    )
    assert "external_id" in multitsframe.columns
    assert multitsframe["external_id"].to_numpy().tolist() == ["AA", "BB", "AA", "AA", "BB", "CCC"]
    assert "channel_id" in multitsframe.columns

    multitsframe = base_multitsframe.copy()
    multitsframe = add_columns_from_metric_metadata(
        multitsframe, replace_metric_col_with_key=["structured_metadata", "metric", "external_id"]
    )
    assert multitsframe["metric"].to_numpy().tolist() == ["AA", "BB", "AA", "AA", "BB", "c"]
    assert "external_id" not in multitsframe.columns
