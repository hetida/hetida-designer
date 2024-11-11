"""Measure cpu bound execution

# Measure cpu bound execution

A component helping measuring actual execution time for a simulated
cpu bound task, i.e. separately from IO. This means it runs synchronous cpu
bound code and measures the time that takes.

You may run this component multiple times in parallel to measure / ensure
performance in your cluster and obtain information in distribution of jobs
over runtime instances and time.

### Inputs:
* **bind**: Allowed values: "single", "multi". Whether a single cpu heavy task
    is run (GIL-restriced) versus a task employing all available CPUs
    (GIL-releasing numpy operation).
* **rounds**: An integer influencing how long that task takes.
    For bind=="single" 10000000 is a good start value.
    For bind=="multi" 10000 is a good start.
    Be careful since high values especially for multi can lead very fast to a
    lot of memory consumption and CPU usage.


"""

import datetime
import random

import numpy as np


def single_cpu_bound(n=10000000):
    start = datetime.datetime.now(datetime.timezone.utc)
    for _ in range(n):
        random.random()  # noqa: S311
    end = datetime.datetime.now(datetime.timezone.utc)
    duration = end - start
    return start, end, duration


def multi_cpu_bound(n=10000):
    start = datetime.datetime.now(datetime.timezone.utc)
    A = np.random.random_sample((n, n))
    B = np.random.random_sample((n, n))
    np.dot(A, B)
    end = datetime.datetime.now(datetime.timezone.utc)
    duration = end - start
    return start, end, duration


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "rounds": {"data_type": "INT"},
        "bind": {"data_type": "STRING"},
    },
    "outputs": {
        "duration": {"data_type": "FLOAT"},
        "start": {"data_type": "STRING"},
        "end": {"data_type": "STRING"},
    },
    "name": "CPU bound",
    "category": "Test",
    "description": "Measure simulated cpu bound execution time",
    "version_tag": "1.0.0",
    "id": "6cdc2d34-69e0-408a-bae9-b156391d9b9d",
    "revision_group_id": "5f9f4b0a-70aa-44d8-9934-63208eb7041e",
    "state": "RELEASED",
    "released_timestamp": "2024-01-10T13:29:19.708481+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, rounds, bind):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    if bind.lower() == "single":
        start, end, duration = single_cpu_bound(rounds)
        return {
            "duration": duration.total_seconds(),
            "start": start.isoformat(),
            "end": end.isoformat(),
        }
    if bind.lower() == "multi":
        start, end, duration = multi_cpu_bound(rounds)
        return {
            "duration": duration.total_seconds(),
            "start": start.isoformat(),
            "end": end.isoformat(),
        }
    raise ValueError(
        'Unknown value of "bind" mode: ' + bind + '. Allowed values are "single" and "multi".'
    )


TEST_WIRING_FROM_PY_FILE_IMPORT = {}
RELEASE_WIRING = {}
