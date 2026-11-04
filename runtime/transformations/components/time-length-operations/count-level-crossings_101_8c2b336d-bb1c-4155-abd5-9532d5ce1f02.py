"""Documentation for Count level crossings

# Count level crossings

## Description
This component counts the level crossings of the input data.

## Inputs
* **data** (Pandas Series): Entries must be numeric.
* **level** (Float): Center of the hysteresis-area.
* **hysteresis** (Float): Width of the tolarance window around **level**, must be non-negative.
* **edge_type** (Float): Input for deciding which type of edges should be counted. Values greater than 0 count ascending level crossings, values smaller than 0 count descending level crossings and equal to 0 all level crossings, respectively.

## Outputs
* **result** (Pandas Series): Series with the number of existing level crossings at the suitable index of data.

## Details
The component counts the level crossings of the given **data**. If the index of data is datetime or numeric, data will be sorted first.

The input **hysteresis** can be used to define a window of tolerance around the input **level**. For example, if level is 5 and hysteresis is 2, values between 4 and 6 will be tolerated.

The input **edge_type** defines which kind of level crossings will be counted. Values greater than 0 will count ascending level crossings, values smaller than 0 descending level crossings and the value 0 all level crossings, respectively.
In the given example with edge_type 1, a change from 0 to 10 will be counted as level crossing. If the edge_type is -1, the same change will not be counted.


## Examples
The json input of a typical call of this component, counting all level crossings is
```
{
        "data": {
                                "2019-08-01T15:20:00": 1.0,
                                "2019-08-01T15:20:10": 7.0,
                                "2019-08-01T15:20:20": 5.0,
                                "2019-08-01T15:20:30": 4.0,
                                "2019-08-01T15:20:40": 2.0,
                                "2019-08-01T15:20:50": 5.0,
                                "2019-08-01T15:21:00": 1.0,
                                "2019-08-01T15:21:10": 8.0,
        },
        "level": 5,
        "hysteresis": 2,
        "edge_type": 0
}
```
The expected output is
```
        "result": {
                                "2019-08-01T15:20:00": 0.0,
                                "2019-08-01T15:20:10": 1.0,
                                "2019-08-01T15:20:20": 1.0,
                                "2019-08-01T15:20:30": 1.0,
                                "2019-08-01T15:20:40": 2.0,
                                "2019-08-01T15:20:50": 2.0,
                                "2019-08-01T15:21:00": 2.0,
                                "2019-08-01T15:21:10": 3.0,
        }
```

The json input of a call of this component with the same data, counting ascending level crossings is
```
{
        "data": {
                                "2019-08-01T15:20:00": 1.0,
                                "2019-08-01T15:20:10": 7.0,
                                "2019-08-01T15:20:20": 5.0,
                                "2019-08-01T15:20:30": 4.0,
                                "2019-08-01T15:20:40": 2.0,
                                "2019-08-01T15:20:50": 5.0,
                                "2019-08-01T15:21:00": 1.0,
                                "2019-08-01T15:21:10": 8.0,
        }
        "level": 5
        "hysteresis": 2
        "edge_type": 1
}
```
The expected output is
```
        "result": {
                                "2019-08-01T15:20:00": 0.0,
                                "2019-08-01T15:20:10": 1.0,
                                "2019-08-01T15:20:20": 1.0,
                                "2019-08-01T15:20:30": 1.0,
                                "2019-08-01T15:20:40": 1.0,
                                "2019-08-01T15:20:50": 1.0,
                                "2019-08-01T15:21:00": 1.0,
                                "2019-08-01T15:21:10": 2.0,
        }
```
"""

import numpy as np

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "data": {"data_type": "SERIES"},
        "level": {"data_type": "FLOAT"},
        "hysteresis": {"data_type": "FLOAT"},
        "edge_type": {"data_type": "FLOAT"},
    },
    "outputs": {
        "result": {"data_type": "SERIES"},
    },
    "name": "Count level crossings",
    "category": "Time length operations",
    "description": "Count the level crossings of the input data",
    "version_tag": "1.0.1",
    "id": "8c2b336d-bb1c-4155-abd5-9532d5ce1f02",
    "revision_group_id": "8b8046ec-0817-e314-936c-08e8c5116ef5",
    "state": "RELEASED",
    "released_timestamp": "2025-06-25T09:02:39.662698+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, data, level, hysteresis, edge_type):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    if data.size < 2:
        raise ValueError(f"length of data must be greater than 1, it is {data.size}")

    if hysteresis < 0:
        raise ValueError(f"hysteresis must be non-negative, it is {hysteresis}")

    if not data.index.is_monotonic_increasing:
        raise ValueError("data must be sorted by its index")

    tolerance = hysteresis / 2

    crossings = (data > (level + tolerance)).astype("int64") - (data < (level - tolerance)).astype(
        "int64"
    )
    crossings = crossings[crossings != 0]

    crossings = (crossings.diff().iloc[1:] // 2).astype("int64")

    if edge_type > 0:
        crossings = crossings[crossings == 1]
    elif edge_type < 0:
        crossings = crossings[crossings == -1] / (-1)
    else:
        crossings = np.abs(crossings).fillna(0)
        crossings = crossings[crossings != 0]

    crossings = crossings.cumsum()
    crossings = crossings.reindex(data.index)
    crossings.iloc[0] = 0

    return {"result": crossings.ffill().astype("int64")}


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "data",
            "filters": {
                "value": '{\n    "2019-08-01T15:20:00.000Z": 1.0,\n    "2019-08-01T15:20:10.000Z": 7.0,\n    "2019-08-01T15:20:20.000Z": 5.0,\n    "2019-08-01T15:20:30.000Z": 4.0,\n    "2019-08-01T15:20:40.000Z": 2.0,\n    "2019-08-01T15:20:50.000Z": 5.0,\n    "2019-08-01T15:21:00.000Z": 1.0,\n    "2019-08-01T15:21:10.000Z": 8.0\n}'
            },
        },
        {"workflow_input_name": "level", "filters": {"value": "5"}},
        {"workflow_input_name": "hysteresis", "filters": {"value": "2"}},
        {"workflow_input_name": "edge_type", "filters": {"value": "0"}},
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "data",
            "filters": {
                "value": '{\n    "2019-08-01T15:20:00.000Z": 1.0,\n    "2019-08-01T15:20:10.000Z": 7.0,\n    "2019-08-01T15:20:20.000Z": 5.0,\n    "2019-08-01T15:20:30.000Z": 4.0,\n    "2019-08-01T15:20:40.000Z": 2.0,\n    "2019-08-01T15:20:50.000Z": 5.0,\n    "2019-08-01T15:21:00.000Z": 1.0,\n    "2019-08-01T15:21:10.000Z": 8.0\n}'
            },
        },
        {"workflow_input_name": "level", "filters": {"value": "5"}},
        {"workflow_input_name": "hysteresis", "filters": {"value": "2"}},
        {"workflow_input_name": "edge_type", "filters": {"value": "0"}},
    ]
}
