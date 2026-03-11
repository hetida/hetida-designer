"""Documentation for Infer Window Size

# Infer Window Size

## Description
This component calculates the window size for a given time series and creates a pandas frequency string for it.

## Inputs
* **series** (Pandas Series): Series for which the calculation is supposed to be performed. The indices must be datetimes.
* **min_num_desired_datapoints_in_window** (Integer): Minimum number of datapoints supposed to be in each window.
* **buffer_factor** (Float): Factor to multiply *min_num_desired_datapoints_in_window* with in order to control the expected number of datapoints inside each window.

## Outputs
* **frequency_string** (String): The created pandas frequency string.

## Details
This component calculates the window size for a given time series based on the median time difference between two consecutive datapoints in seconds. This value is assumed to be the expected time difference between two datapoints for the following steps.

The input **min_num_desired_datapoints_in_window** specifies the minimum number of datapoints desired to be inside each window. A reasonable value is 30 to assume sampling normality.

The input **buffer_factor** is a decimal factor by which **min_num_desired_datapoints_in_window** is multiplied before calculating the window size. If the value is 1, the majority of windows are expected to contain this number of datapoints, but depending on the input series, some windows may contain more and some fewer datapoints. To achieve that a larger number of windows contain at least the specified number of datapoints, the **buffer_factor** should be greater than 1. This results in the expected number of datapoints in each window being higher than the specified minimum number. For values smaller than 1, the window size will be correspondingly smaller, so that the windows are expected to contain fewer datapoints than desired.

The calculated median is multiplied with these two inputs and converted into seconds to get the window size.

The result of the calculation is converted into a [pandas frequency string](https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases) to be able to use it as frequency input of pandas functions, e.g. *pandas.DataFrame.rolling*. The string is always in seconds. The format works for both large and small time ranges even though metrics other than seconds might make more sense depending on the individual case.

## Examples
The json input of a typical call of this component is
```
{
    "series": {
        "2022-01-01T00:00:00Z": 1.058,
        "2022-01-01T00:20:48Z": 0.699,
        "2022-01-01T00:41:37Z": 1.08,
        "2022-01-01T01:02:26Z": 1.054,
        "2022-01-01T01:23:15Z": 0.763,
        "2022-01-01T01:44:04Z": 1.034,
        "2022-01-01T02:04:53Z": 0.965,
        "2022-01-01T02:25:42Z": 0.601,
        "2022-01-01T02:46:31Z": 0.933,
        "2022-01-01T03:07:20Z": 1.081,
        "2022-01-01T03:28:09Z": 2.1,
        "2022-01-01T03:48:58Z": 0.988,
        "2022-01-01T04:09:47Z": 0.741,
        "2022-01-01T04:30:36Z": 0.647,
        "2022-01-01T04:51:25Z": 0.556,
        "2022-01-01T05:12:14Z": 0.453,
        "2022-01-01T05:33:03Z": 1.009,
        "2022-01-01T05:53:52Z": 1.72,
        "2022-01-01T06:14:41Z": 1.002,
        "2022-01-01T06:56:19Z": 0.857,
        "2022-01-01T07:17:08Z": 0.864,
        "2022-01-01T07:37:57Z": 0.606,
        "2022-01-01T07:58:46Z": 0.899,
        "2022-01-01T08:40:24Z": 0.62,
        "2022-01-01T10:03:40Z": 0.721,
        "2022-01-01T10:24:29Z": 1.193,
        "2022-01-01T10:45:18Z": 0.833,
        "2022-01-01T11:06:07Z": 2.06,
        "2022-01-01T11:26:56Z": 0.68,
        "2022-01-01T11:47:45Z": 1.136,
        "2022-01-01T12:08:34Z": 0.62,
        "2022-01-01T12:29:23Z": 0.946,
        "2022-01-01T12:50:12Z": 0.746,
        "2022-01-01T13:11:01Z": 0.833,
        "2022-01-01T13:31:50Z": 0.857,
        "2022-01-01T14:13:28Z": 0.947,
        "2022-01-01T14:34:17Z": 0.841,
        "2022-01-01T14:55:06Z": 0.668,
        "2022-01-01T15:15:55Z": 0.675,
        "2022-01-01T15:36:44Z": 0.84,
        "2022-01-01T15:57:33Z": 0.821,
        "2022-01-01T16:18:22Z": 0.625,
        "2022-01-01T16:39:11Z": 1.155,
        "2022-01-01T17:00:00Z": 0.968
    },
    "min_num_desired_datapoints_in_window": 10,
    "buffer_factor": 1.4
}
```
The expected output is
```
{
    "frequency_string": "17486.0S"
}
```
"""

import pandas as pd


def calculate_window_size(
    series: pd.Series, min_num_desired_datapoints_in_window: int, buffer_factor: float
) -> float:
    """Window size calculation.

    Function to calculate the window size in seconds for the analysis of a timeseries with moving
    windows.

    series (Pandas Series): Series for which the calculation is supposed to be performed.
        The indices must be datetimes.
    min_num_desired_datapoints_in_window (Integer): Minimum number of datapoints supposed to be in
        each window.
    buffer_factor (Float): Factor to multiply min_num_desired_datapoints_in_window with in order to
        control the expected number of datapoints inside each window.


    Returns: Calculated window size in seconds.
    """
    if not isinstance(series.index, pd.DatetimeIndex):
        raise TypeError("This component is exclusively for series with Datetime index!")

    median_diff = series.sort_index().index.to_series().diff().median().seconds

    return median_diff * (min_num_desired_datapoints_in_window * buffer_factor)


def create_pandas_frequency_string(number_of_seconds: float) -> str:
    return str(number_of_seconds) + "s"


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "series": {"data_type": "SERIES"},
        "min_num_desired_datapoints_in_window": {"data_type": "INT"},
        "buffer_factor": {"data_type": "FLOAT"},
    },
    "outputs": {
        "frequency_string": {"data_type": "STRING"},
    },
    "name": "Infer Window Size",
    "category": "Statistic",
    "description": "Infers the size to choose for a moving window",
    "version_tag": "1.0.0",
    "id": "4615ec0d-99bd-40ba-a88b-643dd28fa6e7",
    "revision_group_id": "a9614fc3-e7a0-4df1-8a8c-a1c8cadeb84b",
    "state": "RELEASED",
    "released_timestamp": "2022-11-24T17:06:12.073942+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, series, min_num_desired_datapoints_in_window, buffer_factor):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    window_size = calculate_window_size(
        series=series,
        min_num_desired_datapoints_in_window=min_num_desired_datapoints_in_window,
        buffer_factor=buffer_factor,
    )

    return {"frequency_string": create_pandas_frequency_string(window_size)}


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "series",
            "filters": {
                "value": '{\n    "2022-01-01T00:00:00Z": 1.058,\n    "2022-01-01T00:20:48Z": 0.699,\n    "2022-01-01T00:41:37Z": 1.08,\n    "2022-01-01T01:02:26Z": 1.054,\n    "2022-01-01T01:23:15Z": 0.763,\n    "2022-01-01T01:44:04Z": 1.034,\n    "2022-01-01T02:04:53Z": 0.965,\n    "2022-01-01T02:25:42Z": 0.601,\n    "2022-01-01T02:46:31Z": 0.933,\n    "2022-01-01T03:07:20Z": 1.081,\n    "2022-01-01T03:28:09Z": 2.1,\n    "2022-01-01T03:48:58Z": 0.988,\n    "2022-01-01T04:09:47Z": 0.741,\n    "2022-01-01T04:30:36Z": 0.647,\n    "2022-01-01T04:51:25Z": 0.556,\n    "2022-01-01T05:12:14Z": 0.453,\n    "2022-01-01T05:33:03Z": 1.009,\n    "2022-01-01T05:53:52Z": 1.72,\n    "2022-01-01T06:14:41Z": 1.002,\n    "2022-01-01T06:56:19Z": 0.857,\n    "2022-01-01T07:17:08Z": 0.864,\n    "2022-01-01T07:37:57Z": 0.606,\n    "2022-01-01T07:58:46Z": 0.899,\n    "2022-01-01T08:40:24Z": 0.62,\n    "2022-01-01T10:03:40Z": 0.721,\n    "2022-01-01T10:24:29Z": 1.193,\n    "2022-01-01T10:45:18Z": 0.833,\n    "2022-01-01T11:06:07Z": 2.06,\n    "2022-01-01T11:26:56Z": 0.68,\n    "2022-01-01T11:47:45Z": 1.136,\n    "2022-01-01T12:08:34Z": 0.62,\n    "2022-01-01T12:29:23Z": 0.946,\n    "2022-01-01T12:50:12Z": 0.746,\n    "2022-01-01T13:11:01Z": 0.833,\n    "2022-01-01T13:31:50Z": 0.857,\n    "2022-01-01T14:13:28Z": 0.947,\n    "2022-01-01T14:34:17Z": 0.841,\n    "2022-01-01T14:55:06Z": 0.668,\n    "2022-01-01T15:15:55Z": 0.675,\n    "2022-01-01T15:36:44Z": 0.84,\n    "2022-01-01T15:57:33Z": 0.821,\n    "2022-01-01T16:18:22Z": 0.625,\n    "2022-01-01T16:39:11Z": 1.155,\n    "2022-01-01T17:00:00Z": 0.968\n}'
            },
        },
        {
            "workflow_input_name": "min_num_desired_datapoints_in_window",
            "filters": {"value": "10"},
        },
        {"workflow_input_name": "buffer_factor", "filters": {"value": "1.4"}},
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "series",
            "filters": {
                "value": '{\n    "2022-01-01T00:00:00Z": 1.058,\n    "2022-01-01T00:20:48Z": 0.699,\n    "2022-01-01T00:41:37Z": 1.08,\n    "2022-01-01T01:02:26Z": 1.054,\n    "2022-01-01T01:23:15Z": 0.763,\n    "2022-01-01T01:44:04Z": 1.034,\n    "2022-01-01T02:04:53Z": 0.965,\n    "2022-01-01T02:25:42Z": 0.601,\n    "2022-01-01T02:46:31Z": 0.933,\n    "2022-01-01T03:07:20Z": 1.081,\n    "2022-01-01T03:28:09Z": 2.1,\n    "2022-01-01T03:48:58Z": 0.988,\n    "2022-01-01T04:09:47Z": 0.741,\n    "2022-01-01T04:30:36Z": 0.647,\n    "2022-01-01T04:51:25Z": 0.556,\n    "2022-01-01T05:12:14Z": 0.453,\n    "2022-01-01T05:33:03Z": 1.009,\n    "2022-01-01T05:53:52Z": 1.72,\n    "2022-01-01T06:14:41Z": 1.002,\n    "2022-01-01T06:56:19Z": 0.857,\n    "2022-01-01T07:17:08Z": 0.864,\n    "2022-01-01T07:37:57Z": 0.606,\n    "2022-01-01T07:58:46Z": 0.899,\n    "2022-01-01T08:40:24Z": 0.62,\n    "2022-01-01T10:03:40Z": 0.721,\n    "2022-01-01T10:24:29Z": 1.193,\n    "2022-01-01T10:45:18Z": 0.833,\n    "2022-01-01T11:06:07Z": 2.06,\n    "2022-01-01T11:26:56Z": 0.68,\n    "2022-01-01T11:47:45Z": 1.136,\n    "2022-01-01T12:08:34Z": 0.62,\n    "2022-01-01T12:29:23Z": 0.946,\n    "2022-01-01T12:50:12Z": 0.746,\n    "2022-01-01T13:11:01Z": 0.833,\n    "2022-01-01T13:31:50Z": 0.857,\n    "2022-01-01T14:13:28Z": 0.947,\n    "2022-01-01T14:34:17Z": 0.841,\n    "2022-01-01T14:55:06Z": 0.668,\n    "2022-01-01T15:15:55Z": 0.675,\n    "2022-01-01T15:36:44Z": 0.84,\n    "2022-01-01T15:57:33Z": 0.821,\n    "2022-01-01T16:18:22Z": 0.625,\n    "2022-01-01T16:39:11Z": 1.155,\n    "2022-01-01T17:00:00Z": 0.968\n}'
            },
        },
        {
            "workflow_input_name": "min_num_desired_datapoints_in_window",
            "filters": {"value": "10"},
        },
        {"workflow_input_name": "buffer_factor", "filters": {"value": "1.4"}},
    ]
}
