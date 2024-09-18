"""Documentation for Alerts from Score

# Alerts from Score

## Description

This component generates a Series indicating starts and ends of anomalous situations.

## Inputs
- **scores** (Pandas Series): Should have a datetime index and float values.
- **threshold** (Float): The value above which a score value is considered anomal.

## Outputs
- **alerts** (Pandas Series): The resulting series of alert indications:
    - 1 indicates a start of an anormal situation
      (first anormal data point after a normal datapoints),
    - -1 indicates an end of an anormal situation
      (first normal data point after an anormal data points),
    - 0 indicates no change of state.

## Details
Takes the given score values and compares them to the given threshold.
Values greater than the threshold are considered anormal.
This is used to return a series of values of -1, 0, or 1 indicating alert stops (-1) and starts (1),
respectively (see output description above for details).

For example if you send in a Series of values
```
[0.2, 0.3, 1.2, 1.7, 1.9, 1.8, 1.1, 0.9, 0.5]
```
and a threshold of 1.0 you get back a Series of values
```
[0, 0, 1, 0, 0, 0, 0, -1, 0]
```
which can be interpreted as an alert starting at the third and ending at the seventh entry.

## Examples
The json input of a typical call of this component is
```
{
    "threshold": 42,
    "scores": {
        "2020-01-01T01:15:27.000Z": 42.2,
        "2020-01-03T08:20:03.000Z": 18.7,
        "2020-01-03T08:20:04.000Z": 25.9
    }
}
```
"""

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "scores": {"data_type": "SERIES"},
        "threshold": {"data_type": "FLOAT"},
    },
    "outputs": {
        "alerts": {"data_type": "SERIES"},
    },
    "name": "Alerts from Score",
    "category": "Anomaly Detection",
    "description": "Generate a Series indicating starts and ends of anomalous situations",
    "version_tag": "1.0.0",
    "id": "38f168ef-cb06-d89c-79b3-0cd823f32e9d",
    "revision_group_id": "38f168ef-cb06-d89c-79b3-0cd823f32e9d",
    "state": "RELEASED",
    "released_timestamp": "2022-02-09T17:33:29.236535+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, scores, threshold):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    alerts = (scores > threshold).astype(int).diff(1).fillna(0)
    alerts.name = "alerts"

    return {"alerts": alerts}


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "scores",
            "filters": {
                "value": '{\n    "2020-01-01T01:15:27.000Z": 42.2,\n    "2020-01-03T08:20:03.000Z": 18.7,\n    "2020-01-03T08:20:04.000Z": 25.9\n}'
            },
        },
        {"workflow_input_name": "threshold", "filters": {"value": "42"}},
    ]
}
RELEASE_WIRING = None
