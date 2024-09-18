"""Documentation for Interpolate Timeseries

# Interpolate Timeseries

## Description
Interpolates values in a timeseries at positions specified by a filter series.
Filter series can contain additional positions not present in the original timeseries.

## Inputs
* **timeseries** (SERIES): A pandas Series object with DateTime Index. This is the timeseries
  in which one wants to interpolate. Its values should be float for the typically chosen
  interpolation methods.
* **filter_series** (SERIES): A pandas Series with DateTime Index and boolean values.
  Interpolation will be done at those positions where filter_series is True.
  May include positions not present in timeseries.
* **interpolation_params** (ANY): A dictionary that is passed to the
  [interpolate method](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.Series.interpolate.html). It defaults to selecting `time` as interpolation method. You can choose methods expecting a numerical index, the component handles necessary index transformations.

## Outputs
* **interpolated_timeseries** (SERIES): The complete resulting timeseries with old values and interpolated values.
* **new_values** (SERIES): Only the new values added by interpolation

## Details
Interpolates a timeseries using a parametrizable method, defaulting to linear interpolation.

To determine at which positions new values should be interpolated, a filter_series is used. New values are computed everywhere where filter_series is True, including positions not present in timeseries. This allows to interpolate gaps.

Note that index is transformed to-and-back a numerical index if necessary for the selected interpolation method. Hence you can use all interpolation methods provided by the respective pandas [method](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.Series.interpolate.html).

One interesting entry you can provide in interpolation_params is `"limit_direction": "both"`. This fills values at beginning and end where interpolation is not possible with the first / respective last value.

## Example

If timeseries is
```json
{
    "2018-05-19T22:20:00.000Z": 4.0,
    "2018-05-19T22:25:00.000Z": 5.0,
    "2018-05-19T22:30:00.000Z": 6.0,
    "2018-05-19T22:35:00.000Z": 0.0,
    "2018-05-19T22:40:00.000Z": 0.0,
    "2018-05-19T22:45:00.000Z": 0,
    "2018-05-19T22:50:00.000Z": 0,
    "2018-05-19T22:55:00.000Z": 4,
    "2018-05-19T23:00:00.000Z": 3,
    "2018-05-19T23:05:00.000Z": 2
}
```
and filter_series is
```json
{
    "2018-05-19T22:20:00.000Z": false,
    "2018-05-19T22:25:00.000Z": false,
    "2018-05-19T22:30:00.000Z": false,
    "2018-05-19T22:35:00.000Z": true,
    "2018-05-19T22:40:00.000Z": true,
    "2018-05-19T22:45:00.000Z": true,
    "2018-05-19T22:50:00.000Z": true,
    "2018-05-19T22:55:00.000Z": false,
    "2018-05-19T23:00:00.000Z": false,
    "2018-05-19T23:05:00.000Z": false
}
```
with default value for interpolation_params, implying linear interpolation, the result is:
```
{
    "2018-05-19T22:20:00.000Z": 4,
    "2018-05-19T22:25:00.000Z": 5,
    "2018-05-19T22:30:00.000Z": 6,
    "2018-05-19T22:35:00.000Z": 5.6,
    "2018-05-19T22:40:00.000Z": 5.2,
    "2018-05-19T22:45:00.000Z": 4.8,
    "2018-05-19T22:50:00.000Z": 4.4,
    "2018-05-19T22:55:00.000Z": 4,
    "2018-05-19T23:00:00.000Z": 3,
    "2018-05-19T23:05:00.000Z": 2
}
```
"""  # noqa: E501

# add your own imports here, e.g.
import numpy as np
import pandas as pd

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "timeseries": {"data_type": "SERIES"},
        "filter_series": {"data_type": "SERIES"},
        "interpolation_params": {
            "data_type": "ANY",
            "default_value": {"method": "time"},
        },
    },
    "outputs": {
        "interpolated_timeseries": {"data_type": "SERIES"},
        "new_values": {"data_type": "SERIES"},
    },
    "name": "Interpolate Timeseries",
    "category": "Data Quality",
    "description": "Interpolate a timeseries at filtered positions",
    "version_tag": "0.1.4",
    "id": "47c145cb-acce-442e-9f57-31446172a49a",
    "revision_group_id": "ee2eb771-be37-44a4-b8f3-8a5414aff234",
    "state": "RELEASED",
    "released_timestamp": "2024-02-22T15:06:41.723524+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(
    *,
    timeseries,
    filter_series,
    interpolation_params=parse_default_value(COMPONENT_INFO, "interpolation_params"),
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    combined_index = timeseries.index.union(filter_series.index, sort=True)

    full_filter_series = pd.Series(False, index=combined_index)

    filter_series_true = filter_series[filter_series]
    full_filter_series.loc[filter_series_true.index] = True

    prepared_ts = pd.Series(np.nan, index=combined_index)

    prepared_ts[timeseries.index] = timeseries
    prepared_ts[full_filter_series] = np.nan

    if interpolation_params.get("method", None) != "time" and isinstance(
        prepared_ts.index, pd.DatetimeIndex
    ):
        index_series = pd.Series(prepared_ts.index, index=prepared_ts.index)
        time_diffs = (
            (index_series - index_series.shift(1))
            .fillna(pd.Timedelta(seconds=0))
            .dt.total_seconds()
        )
        interpol_index = time_diffs.cumsum()

    else:
        interpol_index = prepared_ts.index

    prepared_numeric_index = pd.Series(prepared_ts.values, index=interpol_index.values)

    interpolated = pd.Series(
        prepared_numeric_index.interpolate(**interpolation_params).values,
        index=combined_index,
    )

    new_values = interpolated[full_filter_series]

    return {"interpolated_timeseries": interpolated, "new_values": new_values}


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "timeseries",
            "filters": {
                "value": '{\n    "2018-05-19T22:20:00.000Z": 4.0,\n    "2018-05-19T22:25:00.000Z": 5.0,\n    "2018-05-19T22:30:00.000Z": 6.0,\n    "2018-05-19T22:35:00.000Z": 0.0,\n    "2018-05-19T22:40:00.000Z": 0.0,\n    "2018-05-19T22:45:00.000Z": 0,\n    "2018-05-19T22:50:00.000Z": 0,\n    "2018-05-19T22:55:00.000Z": 4,\n    "2018-05-19T23:00:00.000Z": 3,\n    "2018-05-19T23:05:00.000Z": 2\n}'
            },
        },
        {
            "workflow_input_name": "filter_series",
            "filters": {
                "value": '{\n    "2018-05-19T22:15:00.000Z": true,\n    "2018-05-19T22:20:00.000Z": false,\n    "2018-05-19T22:25:00.000Z": false,\n    "2018-05-19T22:30:00.000Z": false,\n    "2018-05-19T22:35:00.000Z": true,\n    "2018-05-19T22:40:00.000Z": true,\n    "2018-05-19T22:45:00.000Z": true,\n    "2018-05-19T22:50:00.000Z": true,\n    "2018-05-19T22:55:00.000Z": false,\n    "2018-05-19T23:00:00.000Z": false,\n    "2018-05-19T23:05:00.000Z": false\n}'
            },
        },
        {
            "workflow_input_name": "interpolation_params",
            "filters": {"value": '{"method": "time", "limit_direction": "both"}'},
        },
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "timeseries",
            "filters": {
                "value": '{\n    "2018-05-19T22:20:00.000Z": 4.0,\n    "2018-05-19T22:25:00.000Z": 5.0,\n    "2018-05-19T22:30:00.000Z": 6.0,\n    "2018-05-19T22:35:00.000Z": 0.0,\n    "2018-05-19T22:40:00.000Z": 0.0,\n    "2018-05-19T22:45:00.000Z": 0,\n    "2018-05-19T22:50:00.000Z": 0,\n    "2018-05-19T22:55:00.000Z": 4,\n    "2018-05-19T23:00:00.000Z": 3,\n    "2018-05-19T23:05:00.000Z": 2\n}'
            },
        },
        {
            "workflow_input_name": "filter_series",
            "filters": {
                "value": '{\n    "2018-05-19T22:15:00.000Z": true,\n    "2018-05-19T22:20:00.000Z": false,\n    "2018-05-19T22:25:00.000Z": false,\n    "2018-05-19T22:30:00.000Z": false,\n    "2018-05-19T22:35:00.000Z": true,\n    "2018-05-19T22:40:00.000Z": true,\n    "2018-05-19T22:45:00.000Z": true,\n    "2018-05-19T22:50:00.000Z": true,\n    "2018-05-19T22:55:00.000Z": false,\n    "2018-05-19T23:00:00.000Z": false,\n    "2018-05-19T23:05:00.000Z": false\n}'
            },
        },
        {
            "workflow_input_name": "interpolation_params",
            "filters": {"value": '{"method": "time", "limit_direction": "both"}'},
        },
    ]
}
