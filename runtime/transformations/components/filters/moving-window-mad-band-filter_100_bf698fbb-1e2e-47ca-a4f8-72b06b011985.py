"""Documentation for Moving Window MAD Band Filter

# Moving Window MAD Band Filter

## Description
This component detects outliers based on calculated bandpass filter statistics. These statistics include the median and median absolute deviation (MAD) for a moving window.

## Inputs
* **series** (Pandas Series): Series to perform the bandpass filter calculation for. The indices must be datetimes.
* **window_size** (String): Time period of each window. Must be a pandas frequency string.
* **min_num_datapoints_in_window** (Integer): Minimum number of datapoints required in a window to calculate the statistics.
* **mad_scaling_factor** (Float): The calculated MADs are multiplied by this factor to adjust the width of the bandfilter at each point. The value 1.4836 makes it equivalent to the standard deviation.
* **min_band_width_factor** (Float): Factor to calculate the minimum band width. The factor is multiplied with the median of the calculated MADs.

## Outputs
* **band_filter_dataframe** (Pandas DataFrame): Data frame with the input series, the calculated statistics and the filter mask.
* **filter_mask** (Pandas Series): Series with the filter mask.

## Details
This component detects outlier in a series based on bandpass filter statistics that it calculates. This includes the calculation of the median and median absolute deviation (MAD) for a moving window of size **window_size**. There must be at least **min_num_datapoints_in_window** datapoints within a window to perform a calculation. If there are fewer datapoints in a window, no calculation is performed.

The function to calculate the MAD is selected based on the size of the series. Both available functions are based on numpy functions. If the size of the series exceeds 10,000 datapoints, numba just-in-time compilation is used to speed up the MAD calculation. The limit of 10,000 datapoints was chosen as result of runtime tests on multiple machines.

The calculated MADs are multiplied by **mad_normalization_constant**. This allows a normalization with regard to other figures. For example, the result with the constant 1.4826 is equivalent to the standard deviation.

A minimum width of the band is ensured using **min_band_width_factor**. The higher the value, the wider the band. The factor is multiplied with the median of the calculated MADs of all windows. All MADs that are smaller than the product are set to it.

The last step is to check which datapoints lie outside of the band. If no calculation was performed for a datapoint because too few datapoints were inside the corresponding window, no statement can be made about this datapoint. In this case, the datapoint is classified as normal and not as an outlier.

The component has two outputs, a data frame with the input series, the calculated statistics, and the result of the last check as well as a series with only the result of the last check. The data frame **band_filter_dataframe** can be used for visualization of the results and the series **filter_mask** to filter the time series.

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
    "window_size": "17486.0S",
    "min_num_datapoints_in_window": 10,
    "mad_scaling_factor": 4.4478,
    "min_band_width_factor": 1
}
```
The expected output is
```
{
    "band_filter_dataframe": {
        "values": {
            "2022-01-01T00:00:00.000Z":1.058,
            "2022-01-01T00:20:48.000Z":0.699,
            "2022-01-01T00:41:37.000Z":1.08,
            "2022-01-01T01:02:26.000Z":1.054,
            "2022-01-01T01:23:15.000Z":0.763,
            "2022-01-01T01:44:04.000Z":1.034,
            "2022-01-01T02:04:53.000Z":0.965,
            "2022-01-01T02:25:42.000Z":0.601,
            "2022-01-01T02:46:31.000Z":0.933,
            "2022-01-01T03:07:20.000Z":1.081,
            "2022-01-01T03:28:09.000Z":2.1,
            "2022-01-01T03:48:58.000Z":0.988,
            "2022-01-01T04:09:47.000Z":0.741,
            "2022-01-01T04:30:36.000Z":0.647,
            "2022-01-01T04:51:25.000Z":0.556,
            "2022-01-01T05:12:14.000Z":0.453,
            "2022-01-01T05:33:03.000Z":1.009,
            "2022-01-01T05:53:52.000Z":1.72,
            "2022-01-01T06:14:41.000Z":1.002,
            "2022-01-01T06:56:19.000Z":0.857,
            "2022-01-01T07:17:08.000Z":0.864,
            "2022-01-01T07:37:57.000Z":0.606,
            "2022-01-01T07:58:46.000Z":0.899,
            "2022-01-01T08:40:24.000Z":0.62,
            "2022-01-01T10:03:40.000Z":0.721,
            "2022-01-01T10:24:29.000Z":1.193,
            "2022-01-01T10:45:18.000Z":0.833,
            "2022-01-01T11:06:07.000Z":2.06,
            "2022-01-01T11:26:56.000Z":0.68,
            "2022-01-01T11:47:45.000Z":1.136,
            "2022-01-01T12:08:34.000Z":0.62,
            "2022-01-01T12:29:23.000Z":0.946,
            "2022-01-01T12:50:12.000Z":0.746,
            "2022-01-01T13:11:01.000Z":0.833,
            "2022-01-01T13:31:50.000Z":0.857,
            "2022-01-01T14:13:28.000Z":0.947,
            "2022-01-01T14:34:17.000Z":0.841,
            "2022-01-01T14:55:06.000Z":0.668,
            "2022-01-01T15:15:55.000Z":0.675,
            "2022-01-01T15:36:44.000Z":0.84,
            "2022-01-01T15:57:33.000Z":0.821,
            "2022-01-01T16:18:22.000Z":0.625,
            "2022-01-01T16:39:11.000Z":1.155,
            "2022-01-01T17:00:00.000Z":0.968
        },
        "band_center":{
            "2022-01-01T00:41:37.000Z":0.9995,
            "2022-01-01T01:02:26.000Z":1.034,
            "2022-01-01T01:23:15.000Z":1.011,
            "2022-01-01T01:44:04.000Z":0.988,
            "2022-01-01T02:04:53.000Z":0.9765,
            "2022-01-01T02:25:42.000Z":0.965,
            "2022-01-01T02:46:31.000Z":0.949,
            "2022-01-01T03:07:20.000Z":0.949,
            "2022-01-01T03:28:09.000Z":0.949,
            "2022-01-01T03:48:58.000Z":0.9765,
            "2022-01-01T04:09:47.000Z":0.965,
            "2022-01-01T04:30:36.000Z":0.933,
            "2022-01-01T04:51:25.000Z":0.933,
            "2022-01-01T05:12:14.000Z":0.864,
            "2022-01-01T05:33:03.000Z":0.864,
            "2022-01-01T05:53:52.000Z":0.8605,
            "2022-01-01T06:14:41.000Z":0.799,
            "2022-01-01T06:56:19.000Z":0.8605,
            "2022-01-01T10:03:40.000Z":0.866,
            "2022-01-01T10:24:29.000Z":0.7895,
            "2022-01-01T10:45:18.000Z":0.833,
            "2022-01-01T11:06:07.000Z":0.833,
            "2022-01-01T11:26:56.000Z":0.833,
            "2022-01-01T11:47:45.000Z":0.845,
            "2022-01-01T12:08:34.000Z":0.841,
            "2022-01-01T12:29:23.000Z":0.841,
            "2022-01-01T12:50:12.000Z":0.833,
            "2022-01-01T13:11:01.000Z":0.84,
            "2022-01-01T13:31:50.000Z":0.833,
            "2022-01-01T14:13:28.000Z":0.833,
            "2022-01-01T14:34:17.000Z":0.84,
            "2022-01-01T14:55:06.000Z":0.8365,
            "2022-01-01T15:15:55.000Z":0.84,
            "2022-01-01T15:36:44.000Z":0.8405
        },
        "rolling_deviation":{
            "2022-01-01T00:41:37.000Z":0.511497,
            "2022-01-01T01:02:26.000Z":0.511497,
            "2022-01-01T01:23:15.000Z":0.511497,
            "2022-01-01T01:44:04.000Z":0.511497,
            "2022-01-01T02:04:53.000Z":0.511497,
            "2022-01-01T02:25:42.000Z":0.5159448,
            "2022-01-01T02:46:31.000Z":0.7072002,
            "2022-01-01T03:07:20.000Z":0.7072002,
            "2022-01-01T03:28:09.000Z":0.8762166,
            "2022-01-01T03:48:58.000Z":0.756126,
            "2022-01-01T04:09:47.000Z":0.9963072,
            "2022-01-01T04:30:36.000Z":0.8539776,
            "2022-01-01T04:51:25.000Z":0.6582744,
            "2022-01-01T05:12:14.000Z":0.9651726,
            "2022-01-01T05:33:03.000Z":0.644931,
            "2022-01-01T05:53:52.000Z":0.644931,
            "2022-01-01T06:14:41.000Z":0.8272908,
            "2022-01-01T06:56:19.000Z":0.8650971,
            "2022-01-01T10:03:40.000Z":0.9607248,
            "2022-01-01T10:24:29.000Z":0.7249914,
            "2022-01-01T10:45:18.000Z":0.6805134,
            "2022-01-01T11:06:07.000Z":0.511497,
            "2022-01-01T11:26:56.000Z":0.511497,
            "2022-01-01T11:47:45.000Z":0.511497,
            "2022-01-01T12:08:34.000Z":0.511497,
            "2022-01-01T12:29:23.000Z":0.511497,
            "2022-01-01T12:50:12.000Z":0.511497,
            "2022-01-01T13:11:01.000Z":0.511497,
            "2022-01-01T13:31:50.000Z":0.511497,
            "2022-01-01T14:13:28.000Z":0.511497,
            "2022-01-01T14:34:17.000Z":0.511497,
            "2022-01-01T14:55:06.000Z":0.511497,
            "2022-01-01T15:15:55.000Z":0.511497,
            "2022-01-01T15:36:44.000Z":0.5203926
        },
        "filter_mask":{
            "2022-01-01T00:00:00.000Z":true,
            "2022-01-01T00:20:48.000Z":true,
            "2022-01-01T00:41:37.000Z":true,
            "2022-01-01T01:02:26.000Z":true,
            "2022-01-01T01:23:15.000Z":true,
            "2022-01-01T01:44:04.000Z":true,
            "2022-01-01T02:04:53.000Z":true,
            "2022-01-01T02:25:42.000Z":true,
            "2022-01-01T02:46:31.000Z":true,
            "2022-01-01T03:07:20.000Z":true,
            "2022-01-01T03:28:09.000Z":false,
            "2022-01-01T03:48:58.000Z":true,
            "2022-01-01T04:09:47.000Z":true,
            "2022-01-01T04:30:36.000Z":true,
            "2022-01-01T04:51:25.000Z":true,
            "2022-01-01T05:12:14.000Z":true,
            "2022-01-01T05:33:03.000Z":true,
            "2022-01-01T05:53:52.000Z":false,
            "2022-01-01T06:14:41.000Z":true,
            "2022-01-01T06:56:19.000Z":true,
            "2022-01-01T07:17:08.000Z":true,
            "2022-01-01T07:37:57.000Z":true,
            "2022-01-01T07:58:46.000Z":true,
            "2022-01-01T08:40:24.000Z":true,
            "2022-01-01T10:03:40.000Z":true,
            "2022-01-01T10:24:29.000Z":true,
            "2022-01-01T10:45:18.000Z":true,
            "2022-01-01T11:06:07.000Z":false,
            "2022-01-01T11:26:56.000Z":true,
            "2022-01-01T11:47:45.000Z":true,
            "2022-01-01T12:08:34.000Z":true,
            "2022-01-01T12:29:23.000Z":true,
            "2022-01-01T12:50:12.000Z":true,
            "2022-01-01T13:11:01.000Z":true,
            "2022-01-01T13:31:50.000Z":true,
            "2022-01-01T14:13:28.000Z":true,
            "2022-01-01T14:34:17.000Z":true,
            "2022-01-01T14:55:06.000Z":true,
            "2022-01-01T15:15:55.000Z":true,
            "2022-01-01T15:36:44.000Z":true,
            "2022-01-01T15:57:33.000Z":true,
            "2022-01-01T16:18:22.000Z":true,
            "2022-01-01T16:39:11.000Z":true,
            "2022-01-01T17:00:00.000Z":true
        }
    },
    "filter_mask": {
        "2022-01-01T00:00:00.000Z":true,
        "2022-01-01T00:20:48.000Z":true,
        "2022-01-01T00:41:37.000Z":true,
        "2022-01-01T01:02:26.000Z":true,
        "2022-01-01T01:23:15.000Z":true,
        "2022-01-01T01:44:04.000Z":true,
        "2022-01-01T02:04:53.000Z":true,
        "2022-01-01T02:25:42.000Z":true,
        "2022-01-01T02:46:31.000Z":true,
        "2022-01-01T03:07:20.000Z":true,
        "2022-01-01T03:28:09.000Z":false,
        "2022-01-01T03:48:58.000Z":true,
        "2022-01-01T04:09:47.000Z":true,
        "2022-01-01T04:30:36.000Z":true,
        "2022-01-01T04:51:25.000Z":true,
        "2022-01-01T05:12:14.000Z":true,
        "2022-01-01T05:33:03.000Z":true,
        "2022-01-01T05:53:52.000Z":false,
        "2022-01-01T06:14:41.000Z":true,
        "2022-01-01T06:56:19.000Z":true,
        "2022-01-01T07:17:08.000Z":true,
        "2022-01-01T07:37:57.000Z":true,
        "2022-01-01T07:58:46.000Z":true,
        "2022-01-01T08:40:24.000Z":true,
        "2022-01-01T10:03:40.000Z":true,
        "2022-01-01T10:24:29.000Z":true,
        "2022-01-01T10:45:18.000Z":true,
        "2022-01-01T11:06:07.000Z":false,
        "2022-01-01T11:26:56.000Z":true,
        "2022-01-01T11:47:45.000Z":true,
        "2022-01-01T12:08:34.000Z":true,
        "2022-01-01T12:29:23.000Z":true,
        "2022-01-01T12:50:12.000Z":true,
        "2022-01-01T13:11:01.000Z":true,
        "2022-01-01T13:31:50.000Z":true,
        "2022-01-01T14:13:28.000Z":true,
        "2022-01-01T14:34:17.000Z":true,
        "2022-01-01T14:55:06.000Z":true,
        "2022-01-01T15:15:55.000Z":true,
        "2022-01-01T15:36:44.000Z":true,
        "2022-01-01T15:57:33.000Z":true,
        "2022-01-01T16:18:22.000Z":true,
        "2022-01-01T16:39:11.000Z":true,
        "2022-01-01T17:00:00.000Z":true
    }
}
```
"""

import numpy as np
import numpy.typing as npt
import pandas as pd
from numba import njit


def median_absolute_deviation(data: npt.ArrayLike) -> np.float64:
    """Calculation of the median absolute deviation (MAD) using numpy functions.

    data (Array like): Values for which the MAD is supposed to be calculated. Must be an array or
        an object that can be converted to an array.

    Returns: Calculated MAD.
    """
    return np.median(np.abs(data - np.median(data)))


@njit
def median_absolute_deviation_numba(data: npt.ArrayLike) -> np.float64:
    """Calculation of the median absolute deviation (MAD) using numba just-in-time compilation.

    data (Array like): Values for which the MAD is supposed to be calculated. Must be an array or
        an object that can be converted to an array.

    Returns: Calculated MAD.
    """
    return np.median(np.abs(data - np.median(data)))


def calculate_rolling_median_absolute_deviation(
    series: pd.Series,
    mad_scaling_factor: float,
    window_size: str,
    min_num_datapoints_in_window: int,
) -> pd.Series:
    """Calculate the median absolute deviation (MAD) for a rolling window.

    The used MAD function is selected based on the size of the timeseries. The numba version is
    used for larger series to reduce the runtime. The limit of 10,000 datapoints in a series was
    chosen as result of runtime tests on different machines.

    series (Pandas Series): Series for which the MAD calculation is supposed to be performed.
    mad_scaling_factor (Float): The calculated MADs are multiplied by this factor to adjust the
        width of the bandfilter at each point. The value 1.4836 makes it equivalent to the standard
        deviation.
    window_size (String): Time period of each window. Must be a pandas frequency string.
    min_num_datapoints_in_window (Integer): Minimum number of observations required in a window to
        calculate a value.

    Returns: Series with the calculated MAD for each timestamp.
    """
    if len(series) < 10000:
        scaled_rolling_median_absolute_deviation = mad_scaling_factor * (
            series.rolling(
                window=window_size,
                min_periods=min_num_datapoints_in_window,
                center=True,
            ).apply(median_absolute_deviation, raw=True)
        )
    else:
        scaled_rolling_median_absolute_deviation = mad_scaling_factor * (
            series.rolling(
                window=window_size,
                min_periods=min_num_datapoints_in_window,
                center=True,
            ).apply(median_absolute_deviation_numba, raw=True, engine="numba")
        )

    return scaled_rolling_median_absolute_deviation


def calculate_band_filter_statistics(
    series: pd.Series,
    window_size: str,
    min_num_datapoints_in_window: int,
    mad_scaling_factor: float,
    min_band_width_factor: float,
) -> dict[str, pd.DataFrame | pd.Series]:
    """Calculate the moving window band filter statistics.

    Function to perform the calculation of band filter statistics using moving windows.
    The statistics include the median, MAD and filter mask for each window with a
    minimum size.

    series (Pandas Series): Series for which the statistics are supposed to be calculated.
        The indices must be datetimes.
    window_size (String): Time period of each window. Must be a pandas frequency string.
    min_num_datapoints_in_window (Integer): Minimum number of observations required in a window
        to perform a calculation.
    mad_scaling_factor (Float): The calculated MADs are multiplied by this factor to adjust the
        width of the bandfilter at each point. The value 1.4836 makes it equivalent to the
        standard deviation.
    min_band_width_factor (Float): Factor to calculate the minimum band width. The factor is
        multiplied with the median of the calculated MADs.

    Returns: Series with the calculated moving window band filter statistics.
    """
    if not isinstance(series.index, pd.DatetimeIndex):
        raise TypeError("This component is exclusively for series with Datetime index!")

    # Convert series to data frame.
    band_filter_dataframe = series.to_frame(name="values")

    # Calculate the rolling median.
    band_filter_dataframe["band_center"] = series.rolling(
        window=window_size, min_periods=min_num_datapoints_in_window, center=True
    ).median()

    # Calculate the rolling median absolute deviation.
    band_filter_dataframe["rolling_deviation"] = calculate_rolling_median_absolute_deviation(
        series=series,
        mad_scaling_factor=mad_scaling_factor,
        window_size=window_size,
        min_num_datapoints_in_window=min_num_datapoints_in_window,
    )

    # Set the minimum width of the band.
    min_width = (
        np.median(band_filter_dataframe["rolling_deviation"].dropna()) * min_band_width_factor
    )
    band_filter_dataframe.loc[
        band_filter_dataframe["rolling_deviation"] < min_width, "rolling_deviation"
    ] = min_width

    # Check which datapoints are invalid.
    band_filter_dataframe["filter_mask"] = (
        np.abs(series - band_filter_dataframe["band_center"])
        <= band_filter_dataframe["rolling_deviation"]
    )

    # Set filter_mask to True for all datapoints for which no calculation could be performed
    # to keep them after filtering.
    band_filter_dataframe.loc[band_filter_dataframe["band_center"].isna(), "filter_mask"] = True

    return [band_filter_dataframe, band_filter_dataframe["filter_mask"]]


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "series": {"data_type": "SERIES"},
        "window_size": {"data_type": "STRING"},
        "min_num_datapoints_in_window": {"data_type": "INT"},
        "mad_scaling_factor": {"data_type": "FLOAT"},
        "min_band_width_factor": {"data_type": "FLOAT"},
    },
    "outputs": {
        "band_filter_dataframe": {"data_type": "DATAFRAME"},
        "filter_mask": {"data_type": "SERIES"},
    },
    "name": "Moving Window MAD Band Filter",
    "category": "Filters",
    "description": "Detect outliers by moving window median absolute deviation (MAD) bandpass filter",  # noqa: E501
    "version_tag": "1.0.0",
    "id": "bf698fbb-1e2e-47ca-a4f8-72b06b011985",
    "revision_group_id": "4cf6f5e7-e4de-4714-8929-5206c595a148",
    "state": "RELEASED",
    "released_timestamp": "2022-11-24T17:03:43.549364+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(
    *,
    series,
    window_size,
    min_num_datapoints_in_window,
    mad_scaling_factor,
    min_band_width_factor,
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    band_filter_dataframe, filter_mask = calculate_band_filter_statistics(
        series=series,
        window_size=window_size,
        min_num_datapoints_in_window=min_num_datapoints_in_window,
        mad_scaling_factor=mad_scaling_factor,
        min_band_width_factor=min_band_width_factor,
    )

    return {
        "band_filter_dataframe": band_filter_dataframe,
        "filter_mask": filter_mask,
    }


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "series",
            "filters": {
                "value": '{\n    "2022-01-01T00:00:00Z": 1.058,\n    "2022-01-01T00:20:48Z": 0.699,\n    "2022-01-01T00:41:37Z": 1.08,\n    "2022-01-01T01:02:26Z": 1.054,\n    "2022-01-01T01:23:15Z": 0.763,\n    "2022-01-01T01:44:04Z": 1.034,\n    "2022-01-01T02:04:53Z": 0.965,\n    "2022-01-01T02:25:42Z": 0.601,\n    "2022-01-01T02:46:31Z": 0.933,\n    "2022-01-01T03:07:20Z": 1.081,\n    "2022-01-01T03:28:09Z": 2.1,\n    "2022-01-01T03:48:58Z": 0.988,\n    "2022-01-01T04:09:47Z": 0.741,\n    "2022-01-01T04:30:36Z": 0.647,\n    "2022-01-01T04:51:25Z": 0.556,\n    "2022-01-01T05:12:14Z": 0.453,\n    "2022-01-01T05:33:03Z": 1.009,\n    "2022-01-01T05:53:52Z": 1.72,\n    "2022-01-01T06:14:41Z": 1.002,\n    "2022-01-01T06:56:19Z": 0.857,\n    "2022-01-01T07:17:08Z": 0.864,\n    "2022-01-01T07:37:57Z": 0.606,\n    "2022-01-01T07:58:46Z": 0.899,\n    "2022-01-01T08:40:24Z": 0.62,\n    "2022-01-01T10:03:40Z": 0.721,\n    "2022-01-01T10:24:29Z": 1.193,\n    "2022-01-01T10:45:18Z": 0.833,\n    "2022-01-01T11:06:07Z": 2.06,\n    "2022-01-01T11:26:56Z": 0.68,\n    "2022-01-01T11:47:45Z": 1.136,\n    "2022-01-01T12:08:34Z": 0.62,\n    "2022-01-01T12:29:23Z": 0.946,\n    "2022-01-01T12:50:12Z": 0.746,\n    "2022-01-01T13:11:01Z": 0.833,\n    "2022-01-01T13:31:50Z": 0.857,\n    "2022-01-01T14:13:28Z": 0.947,\n    "2022-01-01T14:34:17Z": 0.841,\n    "2022-01-01T14:55:06Z": 0.668,\n    "2022-01-01T15:15:55Z": 0.675,\n    "2022-01-01T15:36:44Z": 0.84,\n    "2022-01-01T15:57:33Z": 0.821,\n    "2022-01-01T16:18:22Z": 0.625,\n    "2022-01-01T16:39:11Z": 1.155,\n    "2022-01-01T17:00:00Z": 0.968\n}'
            },
        },
        {"workflow_input_name": "window_size", "filters": {"value": "17486.0s"}},
        {
            "workflow_input_name": "min_num_datapoints_in_window",
            "filters": {"value": "10"},
        },
        {"workflow_input_name": "mad_scaling_factor", "filters": {"value": "4.4478"}},
        {"workflow_input_name": "min_band_width_factor", "filters": {"value": "1"}},
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
        {"workflow_input_name": "window_size", "filters": {"value": "17486.0s"}},
        {
            "workflow_input_name": "min_num_datapoints_in_window",
            "filters": {"value": "10"},
        },
        {"workflow_input_name": "mad_scaling_factor", "filters": {"value": "4.4478"}},
        {"workflow_input_name": "min_band_width_factor", "filters": {"value": "1"}},
    ]
}
