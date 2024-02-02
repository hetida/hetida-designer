"""Documentation for component "Gap Detection Intervals"

# Gap Detection Intervals

## Description

Detects gaps in the given series that are larger than the step size and returns a DataFrame with
information about the gaps.

## Inputs

- **timeseries** (Series):
  Expects index of data type DateTimeIndex.

- **start_date_str** (String, default value: null):
  Desired start date of the processing range. Expexcts ISO 8601 format.
  Alternatively, the `timeseries` can have an attribute `ref_interval_start_timestamp` (or `from`)
  that will be used instead.
  If neither is defined, the processing range begins with the first data point in `timeseries`.
  The start date must not be later than the end date.

- **end_date_str** (String, default value: null):
  Desired end date of the processing range. Expexcts ISO 8601 format.
  Alternatively, the `timeseries` can have an attribute `ref_interval_end_timestamp` (or `to`) that
  will be used instead.
  If neither is defined, the processing range ends with the last data point in `timeseries`.
  The start date must not be later than the end date.

- **auto_stepsize** (Boolean, default value: true):
  If true, the function will automatically determine the step size based on the `timeseries` index
  and `step_size_str` must not be set.
  If false, a `step_size_str` must be set.
  If `ref_frequency` is contained in the attributes of `timeseries` this value will be used for the
  `step_size_str` and `auto_stepsize` will be set to false.

- **history_end_date_str** (String, default value: null):
  Only relevant when `auto_stepsize` is true.
  Expects a date string  between start_date and end_date in ISO 8601 format.
  The desired end date for the training data used to determine the step unit.
  If not specified, the entire
  processing range is used as training data.

- **percentile** (Float, default value: 0.5):
  Only relevant when `auto_stepsize` is true.
  Expects a positive value smaller than or equal to 1. The percentile value to use for automatic
  determination of the expected gapsize between two consecutive data points. The value should be
  selected according to the expected ratio of gaps to regular steps. I.e. if it is to be expected
  that more than 50% of the time steps are gaps, the value should be reduced; if fewer gaps are to
  be expected, the value can be adjusted upwards accordingly.

- **interpolation_method** (String, default value: nearest):
  Only relevant when `auto_stepsize` is true.
  Is used to determine the percentile value via the Pandas `quantile` method.
  Thus, must be one of `linear`, `lower`, `higher`, `midpoint`, `nearest`.

- **min_amount_datapoints** (Int, default value: 11):
  Only relevant when `auto_stepsize` is True.
  Expects a positive value. Minimum amount of datapoints required. Effects the expectable precision
  of the `percentile` value.

- **step_size_str** (String, default value: null):
  Must not be set if `auto_stepsize` is true, but must be set if `auto_stepsize` is false.
  The expected time step between consecutive timestamps in the time series. Must be a frequency
  string, e.g. "D" or "60s".

- **step_size_factor** (Float, default value: 1.0):
  Expects a positive value. The value is used to define when a step between two consecutive data
  points is recognized as a gap. I.e. a value of 1.0 means that all steps larger than the
  specified or determined step size are recognized as gaps, while a value of 2.0 means that steps
  are only recognized as gaps if they are more than twice as large as the specified or determined
  step size.

## Outputs

- **gap_info** (DataFrame):
  A DataFrame containing the beginning and end timestamps of gaps larger than the determined or
  given step size.
  Columns are:
  - "start" (Timestamp): Start index of the gap.
  - "end" (Timestamp): End index of the gap.
  - "start_inclusive" (Boolean): Defines whether the start boundary is inclusive or not.
  - "end_inclusive" (Boolean): Defines whether the start boundary is inclusive or not.
  - "gap_size" (Timedelta): Size of the gap
  - "value_to_left" (Float/Int): If existing, last value before the gap, otherwise None
  - "value_to_right" (Float/Int): If existing, first value after the gap, otherwise None
  - "mean_left_right" (Float/Int): The mean value of the `value_to_left` and `value_to_right`.
    None, if at least one of these values is None.

## Details

If **start_date_str** (or **end_date_str**) is not zero, check whether it is contained in the
**time series** and add it if necessary, and remove all data points with an earlier (or later)
index in order to reduce the **time series** to the processing range.

To detect gaps, the time intervals between consecutive data points are determined.
If **auto_stepsize** is set to true, determine the step size using the **percentile**-th quantile of
the time intervals in the training range.
The training range is determined by the **start_date_str** and the **history_end_date_str**.
If the latter is not defined, the full processing range is used as the training range.
If **auto_stepsize` is set to false, the step size is defined by the **step_size_str**.
If a time interval is greater than the product of the **step_size_factor** and the step size, it is
considered a gap.

For each gap, the output DataFrame **gap_info** contains the index of the preceding (following,
respectively) data point, the information as to whether the indices belong to the gap and, if
present, the corresponding values.
If both the value to the left and the value to the right of the gap are of the float or int data
type, the arithmetic mean of the two values is also provided.
"""

from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, validator

from hetdesrun.runtime.exceptions import ComponentInputValidationException


def timestamp_str_to_pd_timestamp(timestamp: str, input_name: str) -> pd.Timestamp:
    try:
        date = pd.to_datetime(timestamp, utc=True)
    except ValueError as error:
        raise ComponentInputValidationException(
            str(error), error_code=422, invalid_component_inputs=[input_name]
        ) from error
    return date


def freqstr2dateoffset(freqstr: str) -> pd.DateOffset:
    """Transform frequency string to Pandas DateOffset."""
    return pd.tseries.frequencies.to_offset(freqstr)


def freqstr2timedelta(freqstr: str, input_name: str) -> pd.Timedelta:
    """Transform frequency string to Pandas Timedelta."""
    try:
        return pd.to_timedelta(freqstr)
    except ValueError:
        try:
            return pd.to_timedelta(freqstr2dateoffset(freqstr))
        except TypeError as err:
            raise ComponentInputValidationException(
                f"The step_size_str cannot be parsed as Pandas Timedelta: {str(err)}",
                error_code=422,
                invalid_component_inputs=[input_name],
            ) from err


class GapDetectionParameters(BaseModel):
    start_date_str: str | None
    start_date: pd.Timestamp | None = None
    end_date_str: str | None
    end_date: pd.Timestamp | None = None
    auto_stepsize: bool
    history_end_date_str: str | None
    history_end_date: pd.Timestamp | None = None
    percentile: float
    interpolation_method: str
    min_amount_datapoints: int
    step_size_str: str | None
    step_size: pd.Timedelta | None = None
    step_size_factor: float
    fill_value: Any

    @validator("start_date")
    def get_start_date_from_start_date_str(
        cls, start_date: pd.Timestamp | None, values: dict  # noqa: ARG002
    ) -> pd.Timestamp | None:
        if values["start_date_str"] is None:
            return None

        return timestamp_str_to_pd_timestamp(values["start_date_str"], "start_date_str")

    @validator("end_date")
    def get_end_date_from_end_date_str(
        cls, end_date: pd.Timestamp | None, values: dict  # noqa: ARG002
    ) -> pd.Timestamp | None:
        if values["end_date_str"] is None:
            return None

        return timestamp_str_to_pd_timestamp(values["end_date_str"], "end_date_str")

    @validator("end_date")
    def verify_end_date_later_than_start_date(
        cls, end_date: pd.Timestamp | None, values: dict
    ) -> pd.Timestamp | None:
        start_date = values["start_date"]
        if None not in (start_date, end_date) and start_date > end_date:
            raise ComponentInputValidationException(
                "The value start_date must not be later than the end_date, while it is "
                f"{start_date} > {end_date}.",
                error_code=422,
                invalid_component_inputs=["end_date_str", "start_date_str"],
            )
        return end_date

    @validator("history_end_date")
    def get_history_end_date_from_history_end_date_str(
        cls, history_end_date: pd.Timestamp | None, values: dict  # noqa: ARG002
    ) -> pd.Timestamp | None:
        if values["history_end_date_str"] is None:
            return None

        return timestamp_str_to_pd_timestamp(
            values["history_end_date_str"], "history_end_date_str"
        )

    @validator("history_end_date")
    def verify_history_end_date_between_start_date_and_end_date(
        cls, history_end_date: pd.Timestamp | None, values: dict
    ) -> pd.Timestamp | None:
        start_date = values["start_date"]
        end_date = values["end_date"]
        if history_end_date is not None:
            if start_date > history_end_date:
                raise ComponentInputValidationException(
                    "The value history_end_date has to be inbetween start_date and end_date, while "
                    f"it is {history_end_date} < {start_date}.",
                    error_code=422,
                    invalid_component_inputs=["history_end_date_str"],
                )
            if end_date < history_end_date:
                raise ComponentInputValidationException(
                    "The value history_end_date has to be inbetween start_date and end_date, while "
                    f"it is {history_end_date} > {end_date}.",
                    error_code=422,
                    invalid_component_inputs=["history_end_date_str"],
                )
        else:
            history_end_date = None
        return history_end_date

    @validator("percentile")
    def verify_percentile(cls, percentile: float) -> float:
        if (percentile < 0) or (percentile > 1):
            raise ComponentInputValidationException(
                "The percentile value has to be a non-negative float less or equal to 1.",
                error_code=422,
                invalid_component_inputs=["percentile"],
            )
        return percentile

    @validator("interpolation_method")
    def verify_interpolation_method(cls, interpolation_method: str) -> str:
        if interpolation_method not in (
            "linear",
            "lower",
            "higher",
            "midpoint",
            "nearest",
        ):
            raise ComponentInputValidationException(
                "The interpolation method must be one of "
                "`linear`, `lower`, `higher`, `midpoint`, `nearest`",
                error_code=422,
                invalid_component_inputs=["interpolation_method"],
            )
        return interpolation_method

    @validator("min_amount_datapoints")
    def verify_min_amount_datapoints(cls, min_amount_datapoints: int) -> int:
        if min_amount_datapoints < 0:
            raise ComponentInputValidationException(
                "The minimum amount of datapoints has to be a non-negative integer.",
                error_code=422,
                invalid_component_inputs=["min_amount_datapoints"],
            )
        return min_amount_datapoints

    @validator("step_size_str")
    def verify_step_size(cls, step_size_str: str, values: dict) -> str:
        auto_stepsize = values["auto_stepsize"]
        if auto_stepsize is False:
            if step_size_str is None:
                raise ComponentInputValidationException(
                    "A step_size is required for gap detection, "
                    "if it is not automatically determined.",
                    error_code=422,
                    invalid_component_inputs=["step_size_str"],
                )
        elif step_size_str is not None:
            raise ComponentInputValidationException(
                "The step_size must not be set, "
                "if automatical step size determination is enabled.",
                error_code=422,
                invalid_component_inputs=["step_size_str"],
            )
        return step_size_str

    @validator("step_size")
    def get_step_size(
        cls, step_size: pd.Timedelta | None, values: dict  # noqa: ARG002
    ) -> pd.Timedelta | None:
        if values["step_size_str"] is None:
            return None
        return freqstr2timedelta(values["step_size_str"], "step_size_str")

    @validator("step_size_factor")
    def verify_step_size_factor(cls, factor: float) -> float:
        if factor < 0:
            raise ComponentInputValidationException(
                "The gap size factor has to be a non-negative float.",
                error_code=422,
                invalid_component_inputs=["step_size_factor"],
            )
        return factor


def check_add_boundary_dates(
    timeseries: pd.Series,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    fill_value: Any | None = None,
) -> pd.Series:
    if start_date not in timeseries.index:
        timeseries[start_date] = fill_value

    if end_date not in timeseries.index:
        timeseries[end_date] = fill_value

    timeseries = timeseries.sort_index()

    return timeseries


def constrict_series_to_dates(
    timeseries_data: pd.Series | pd.DataFrame,
    start_date: pd.Timestamp | None,
    end_date: pd.Timestamp | None,
) -> pd.Series | pd.DataFrame:
    true_array = np.ones(shape=len(timeseries_data), dtype=bool)
    series_after_start = (
        timeseries_data.index >= start_date if start_date is not None else true_array
    )
    series_before_end = (
        timeseries_data.index <= end_date if start_date is not None else true_array
    )
    return timeseries_data[series_after_start & series_before_end]


def check_amount_datapoints(series: pd.Series, min_amount_datapoints: int) -> None:
    if len(series) < min_amount_datapoints:
        raise ComponentInputValidationException(
            f"The timeseries must contain at least {min_amount_datapoints} datapoints.",
            error_code=422,
            invalid_component_inputs=["timeseries"],
        )


def determine_timestep_gapsize_percentile(
    timeseries_data: pd.Series | pd.DataFrame,
    percentile: float,
    interpolation_method: str,
) -> pd.Timedelta:
    gaps = timeseries_data.index.to_series().diff().dropna()

    percentile_gapsize = gaps.quantile(percentile, interpolation=interpolation_method)

    return percentile_gapsize


def determine_gap_length(
    timeseries: pd.Series, step_size: pd.Timedelta
) -> pd.DataFrame:
    gaps = timeseries.index.to_series().diff().to_numpy()

    stepsize_seconds = step_size.total_seconds()

    normalized_gaps = [
        pd.Timedelta(gap).total_seconds() / stepsize_seconds if pd.notna(gap) else None
        for gap in gaps
    ]

    result_df = pd.DataFrame(
        {"value": timeseries.to_numpy(), "gap": normalized_gaps}, index=timeseries.index
    )

    return result_df


def return_gap_boundary_timestamps(
    frame_with_gapsizes: pd.DataFrame, series: pd.Series, step_size_factor: float = 1.0
) -> pd.DataFrame:
    # Identify rows where gap is greater than 1
    large_gap_indices = frame_with_gapsizes[
        frame_with_gapsizes["gap"] > step_size_factor
    ].index.to_numpy()
    # Extract the start and end timestamps of the gaps
    gap_starts = [
        frame_with_gapsizes.index[index - 1]
        for index, large_gap_index in enumerate(frame_with_gapsizes.index)
        if large_gap_index in large_gap_indices
    ]

    left_values = series[gap_starts].to_numpy()
    right_values = series[large_gap_indices].to_numpy()

    # Create a DataFrame to store the results
    result_df = pd.DataFrame(
        {
            "start": gap_starts,
            "end": large_gap_indices,
            "start_inclusive": False,
            "end_inclusive": False,
            "gap_size": large_gap_indices - gap_starts,
            "value_to_left": left_values,
            "value_to_right": right_values,
            "mean_left_right": np.mean((left_values, right_values), axis=0)
            if pd.api.types.is_numeric_dtype(series) is True
            else None,
        }
    )

    return result_df


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "timeseries": {"data_type": "SERIES"},
        "start_date_str": {"data_type": "STRING", "default_value": None},
        "end_date_str": {"data_type": "STRING", "default_value": None},
        "auto_stepsize": {"data_type": "BOOLEAN", "default_value": True},
        "history_end_date_str": {"data_type": "STRING", "default_value": None},
        "percentile": {"data_type": "FLOAT", "default_value": 0.5},
        "interpolation_method": {"data_type": "STRING", "default_value": "nearest"},
        "min_amount_datapoints": {"data_type": "INT", "default_value": 11},
        "step_size_str": {"data_type": "STRING", "default_value": None},
        "step_size_factor": {"data_type": "FLOAT", "default_value": 1.0},
        "fill_value": {"data_type": "ANY", "default_value": None},
    },
    "outputs": {
        "gap_info": {"data_type": "DATAFRAME"},
    },
    "name": "Gap Detection Intervals",
    "category": "Data Quality",
    "description": "Detects gaps in the given series that are larger than the step size and returns a DataFrame with information about the gaps.",  # noqa: E501
    "version_tag": "1.0.0",
    "id": "cd2a8b7f-a1af-4630-89a5-738af595472a",
    "revision_group_id": "415662ab-e4fb-4084-b752-80433d0df291",
    "state": "DRAFT",
}


def main(
    *,
    timeseries: pd.Series,
    start_date_str: str | None = None,
    end_date_str: str | None = None,
    auto_stepsize=True,
    history_end_date_str: str | None = None,
    percentile: float = 0.5,
    interpolation_method="nearest",
    min_amount_datapoints: int = 11,
    step_size_str: str | None = None,
    step_size_factor: float = 1.0,
    fill_value: Any | None = None,
) -> dict:
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    timeseries = timeseries.sort_index().dropna()

    if start_date_str is None:
        if "ref_interval_start_timestamp" in timeseries.attrs:
            start_date_str = timeseries.attrs["ref_interval_start_timestamp"]
        elif "from" in timeseries.attrs:
            start_date_str = timeseries.attrs["from"]
    if end_date_str is None:
        if "ref_interval_end_timestamp" in timeseries.attrs:
            end_date_str = timeseries.attrs["ref_interval_end_timestamp"]
        elif "to" in timeseries.attrs:
            end_date_str = timeseries.attrs["to"]

    if (
        step_size_str is None
        and not auto_stepsize
        and "ref_frequency" in timeseries.attrs
    ):
        step_size_str = timeseries.attrs["ref_frequency"]
        freqstr2timedelta(step_size_str, 'timeseries.attrs["ref_frequency"]')
        auto_stepsize = False

    input_params = GapDetectionParameters(
        start_date_str=start_date_str,
        end_date_str=end_date_str,
        auto_stepsize=auto_stepsize,
        history_end_date_str=history_end_date_str,
        percentile=percentile,
        min_amount_datapoints=min_amount_datapoints,
        interpolation_method=interpolation_method,
        step_size_str=step_size_str,
        step_size_factor=step_size_factor,
        fill_value=fill_value,
    )
    series_with_bounds = check_add_boundary_dates(
        timeseries, input_params.start_date, input_params.end_date
    )
    constricted_series = constrict_series_to_dates(
        series_with_bounds, input_params.start_date, input_params.end_date
    )

    if auto_stepsize:
        check_amount_datapoints(
            series=constricted_series,
            min_amount_datapoints=input_params.min_amount_datapoints,
        )
        if input_params.history_end_date is not None:
            training_series = constrict_series_to_dates(
                timeseries, input_params.start_date, input_params.history_end_date
            )
        else:
            training_series = constricted_series
        input_params.step_size = determine_timestep_gapsize_percentile(
            training_series, percentile, interpolation_method
        )

    df_with_gaps = determine_gap_length(constricted_series, input_params.step_size)

    return {
        "gap_info": return_gap_boundary_timestamps(
            df_with_gaps, constricted_series, step_size_factor
        )
    }


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "timeseries",
            "adapter_id": "direct_provisioning",
            "filters": {
                "value": (
                    "{\n"
                    '    "2020-01-01T01:15:00.000Z": 10.0,\n'
                    '    "2020-01-01T01:16:00.000Z": 10.0,\n'
                    '    "2020-01-01T01:17:00.000Z": 10.0,\n'
                    '    "2020-01-01T01:18:00.000Z": 10.0,\n'
                    '    "2020-01-01T01:19:00.000Z": 10.0,\n'
                    '    "2020-01-01T01:20:00.000Z": 10.0,\n'
                    '    "2020-01-01T01:21:00.000Z": 10.0,\n'
                    '    "2020-01-02T16:20:00.000Z": 20.0,\n'
                    '    "2020-01-02T16:21:00.000Z": 20.0,\n'
                    '    "2020-01-02T16:22:00.000Z": 20.0,\n'
                    '    "2020-01-02T16:23:00.000Z": 20.0,\n'
                    '    "2020-01-02T16:24:00.000Z": 20.0,\n'
                    '    "2020-01-02T16:25:00.000Z": 20.0,\n'
                    '    "2020-01-02T16:26:00.000Z": 20.0,\n'
                    '    "2020-01-03T08:20:00.000Z": 30.0,\n'
                    '    "2020-01-03T08:21:04.000Z": 30.0,\n'
                    '    "2020-01-03T08:22:00.000Z": 30.0,\n'
                    '    "2020-01-03T08:23:04.000Z": 30.0,\n'
                    '    "2020-01-03T08:24:00.000Z": 30.0,\n'
                    '    "2020-01-03T08:25:04.000Z": 30.0,\n'
                    '    "2020-01-03T08:26:06.000Z": 30.0\n'
                    "}"
                )
            },
        },
    ],
}
