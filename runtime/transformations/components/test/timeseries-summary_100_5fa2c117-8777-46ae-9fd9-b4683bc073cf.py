"""Timeseries Summary

# Timeseries Summary

Compute some summary information of a timeseries (both its values and index) and output
that as a dictionary. Additionally provide some output how fast summary computation was.
"""

import datetime

import pandas as pd

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "series": {"data_type": "SERIES"},
    },
    "outputs": {
        "summary": {"data_type": "ANY"},
        "start": {"data_type": "STRING"},
        "end": {"data_type": "STRING"},
        "duration": {"data_type": "FLOAT"},
    },
    "name": "Timeseries Summary",
    "category": "Test",
    "description": "Summarize some timeseries information",
    "version_tag": "1.0.0",
    "id": "5fa2c117-8777-46ae-9fd9-b4683bc073cf",
    "revision_group_id": "fd964492-f3a9-4a95-8753-1a191571d63d",
    "state": "RELEASED",
    "released_timestamp": "2024-01-10T13:29:19.716925+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, series):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    start = datetime.datetime.now(datetime.timezone.utc)
    summary_dict = {
        "length": len(series),
        "describe": str(
            series.describe(percentiles=(0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95)).to_dict()
        ),
        "num_duplicates": int(series.duplicated().sum()),
        "num_index_duplicates": int(pd.Series(series.index).duplicated().sum()),
        "index": str(series.index),
        "series": str(series),
        "dtype": str(series.dtype),
        "first_value": None if len(series) == 0 else str(series.iloc[0]),
        "first_index": None if len(series) == 0 else str(series.index[0]),
        "last_value": None if len(series) == 0 else str(series.iloc[-1]),
        "last_index": None if len(series) == 0 else str(series.index[-1]),
        "index_distances_describe": str(
            (pd.Series(series.index) - pd.Series(series.index).shift())
            .dropna()
            .describe(percentiles=(0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95))
            .to_dict()
        ),
    }

    end = datetime.datetime.now(datetime.timezone.utc)
    duration = (end - start).total_seconds()

    return {
        "summary": summary_dict,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "duration": duration,
    }


TEST_WIRING_FROM_PY_FILE_IMPORT = {}
RELEASE_WIRING = {}
