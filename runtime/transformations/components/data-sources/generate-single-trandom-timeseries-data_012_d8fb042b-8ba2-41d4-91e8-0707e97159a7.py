"""Documentation for Generate Random Single Timeseries Data

# Generates Random Single Timeseries Data

Generate single timeseries data with some options.

* **frequency**: [Pandas timedelta string](https://pandas.pydata.org/docs/user_guide/timedeltas.html#time-deltas) like "5min".
* **timestampFrom**: start timestamp, [dtexp](https://github.com/stewit/dtexp) expression (like "now -1d") or absolute isoformat timestamp
* **timestampTo**: end timestamp, [dtexp](https://github.com/stewit/dtexp) expression (like "now -1d") or absolute isoformat timestamp
* **random_seed**: Random number generator seed (default: null)
* **offset**: add this to the generated timeseries
* **factor**: multiply the genereated timeseries with this factor
"""

# add your own imports here, e.g.
import datetime

import numpy as np
import pandas as pd

from hetdesrun.dt_utils import resolve_interval

# %%
# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "timestampTo": {"data_type": "STRING"},
        "timestampFrom": {"data_type": "STRING"},
        "frequency": {"data_type": "STRING", "default_value": "5min"},
        "random_seed": {"data_type": "INT", "default_value": None},
        "offset": {"data_type": "FLOAT", "default_value": 0.0},
        "factor": {"data_type": "FLOAT", "default_value": 1.0},
    },
    "outputs": {
        "data": {"data_type": "SERIES"},
    },
    "name": "Generate Random Single Timeseries Data",
    "category": "Data Sources",
    "description": "Random single timeseries generator",
    "version_tag": "0.1.2",
    "id": "d8fb042b-8ba2-41d4-91e8-0707e97159a7",
    "revision_group_id": "158bfe32-028c-4e65-97b0-3fbd8ba1ace0",
    "state": "RELEASED",
    "released_timestamp": "2025-12-08T20:59:46.300861+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(
    *,
    timestampTo,
    timestampFrom,
    frequency="5min",
    random_seed=None,
    offset=0.0,
    factor=1.0,
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    # write your function code here.

    rng = np.random.default_rng(seed=random_seed)

    start, end = resolve_interval(timestampFrom, timestampTo)

    dt_range = pd.date_range(
        start=start,
        end=end,
        freq=(frequency.strip() if frequency.strip() != "" else "1h"),
    ).tz_convert(datetime.timezone.utc)

    ts_df = pd.DataFrame(
        {
            "timestamp": dt_range,
            "value": rng.standard_normal(len(dt_range)) * factor + offset,
        }
    )

    return {"data": pd.Series(ts_df["value"].values, index=ts_df["timestamp"])}


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {"workflow_input_name": "timestampTo", "filters": {"value": "now"}},
        {"workflow_input_name": "timestampFrom", "filters": {"value": "now - 1d"}},
        {
            "workflow_input_name": "frequency",
            "use_default_value": True,
            "filters": {"value": "5min"},
        },
        {"workflow_input_name": "random_seed", "filters": {"value": "null"}},
        {
            "workflow_input_name": "offset",
            "use_default_value": True,
            "filters": {"value": "0.0"},
        },
        {
            "workflow_input_name": "factor",
            "use_default_value": True,
            "filters": {"value": "1.0"},
        },
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {"workflow_input_name": "timestampTo", "filters": {"value": "now"}},
        {"workflow_input_name": "timestampFrom", "filters": {"value": "now - 1d"}},
        {
            "workflow_input_name": "frequency",
            "use_default_value": True,
            "filters": {"value": "5min"},
        },
        {"workflow_input_name": "random_seed", "filters": {"value": "null"}},
        {
            "workflow_input_name": "offset",
            "use_default_value": True,
            "filters": {"value": "0.0"},
        },
        {
            "workflow_input_name": "factor",
            "use_default_value": True,
            "filters": {"value": "1.0"},
        },
    ]
}
