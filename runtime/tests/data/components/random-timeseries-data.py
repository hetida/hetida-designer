# add your own imports here, e.g.
import datetime
from copy import deepcopy

import numpy as np
import pandas as pd

# %%
# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "timestampTo": {"data_type": "STRING"},
        "timestampFrom": {"data_type": "STRING"},
        "frequency": {"data_type": "STRING", "default_value": "5min"},
        "metrics": {
            "data_type": "ANY",
            "default_value": ["timeseries1", "timeseries2"],
        },
        "random_seed": {"data_type": "INT", "default_value": None},
        "metrics_parameters": {
            "data_type": "ANY",
            "default_value": {"__DEFAULT__": {"offset": 0.0, "factor": 3.0, "frequency": "1h"}},
        },
    },
    "outputs": {
        "data": {"data_type": "MULTITSFRAME"},
    },
    "name": "Generate Random Timeseries Data",
    "category": "Data Sources",
    "description": "Random timeseries generator",
    "version_tag": "0.1.0",
    "id": "f2a39f6b-3336-44f2-8c4f-2fd0a4651dd0",
    "revision_group_id": "d9eae824-087a-4494-9dda-e22de8066586",
    "state": "DRAFT",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(
    *,
    timestampTo,
    timestampFrom,
    frequency="5min",
    metrics=parse_default_value(COMPONENT_INFO, "metrics"),
    random_seed=None,
    metrics_parameters=parse_default_value(COMPONENT_INFO, "metrics_parameters"),
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    # write your function code here.

    metrics_parameters_to_use = deepcopy(
        COMPONENT_INFO["inputs"]["metrics_parameters"]["default_value"]
    )
    metrics_parameters_to_use.update(metrics_parameters)

    if "__DEFAULT__" not in metrics_parameters_to_use:
        metrics_parameters_to_use["__DEFAULT__"] == {}

    if isinstance(metrics, str):
        metrics = [m.strip() for m in metrics.split(",")]

    rng = np.random.default_rng(seed=random_seed)

    ts_dfs = []
    for ts_id in metrics:
        metric_params_dict = (
            metrics_parameters_to_use[ts_id]
            if ts_id in metrics_parameters_to_use
            else metrics_parameters_to_use["__DEFAULT__"]
        )

        dt_range = pd.date_range(
            start=timestampFrom,
            end=timestampTo,
            freq=frequency.strip()
            if frequency.strip() != ""
            else metric_params_dict.get("frequency", "1h"),
            tz=datetime.timezone.utc,
        )

        offset = metric_params_dict.get("offset", 0.0)
        factor = metric_params_dict.get("factor", 1.0)

        ts_df = pd.DataFrame(
            {
                "timestamp": dt_range,
                "metric": ts_id,
                "value": rng.standard_normal(len(dt_range)) * factor + offset,
            }
        )

        ts_dfs.append(ts_df)

    return {"data": pd.concat(ts_dfs).sort_values("timestamp").reset_index(drop=True)}
