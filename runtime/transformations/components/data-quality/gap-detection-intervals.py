"""Documentation for component "Gap Detection Intervals"

# Gap Detection Intervals

## Description
Detects gaps in the given series that are larger than the step size and returns a DataFrame with
information about the gaps.

## Inputs
- **timeseries** (Series):
    Expects index of data type DateTimeIndex.

- **start_date_str** (String):
    Desired start date of the processing range. Expexcts ISO 8601 format. Alternatively, the
    `timeseries` can have an attribute "start_date" that will be used instead. If neither is
    defined, the processing range begins with the first data point in `timeseries`. The start date
    must not be later than the end date.

- **end_date_str** (String):
    Desired end date of the processing range. Expexcts ISO 8601 format. Alternatively, the
    `timeseries` can have an attribute "end_date" that will be used instead. If neither is defined,
    the processing range ends with the last data point in `timeseries`. The start date must not be
    later than the end date.

- **step_size** (String):
    The expected time step between consecutive timestamps in the time series. Must be a frequency
    string, e.g. "D" or "2h".

- **step_size_factor** (Float):
    Expects a positive value. The value is used to define when a step between two consecutive data
    points is recognized as a gap. I.e. a value of 1.0 means that all steps larger than the
    specified `step_size` are recognized as gaps, while a value of 2.0 means that steps are only
    recognized as gaps if they are more than twice as large as the specified `step_size`.


## Outputs
- **gap_info** (DataFrame) :
    A DataFrame containing the beginning and end timestamps of gaps larger than the determined or
    given step size.
    Columns are:
    - "start" (Timestamp): Start index of the gap.
    - "end" (Timestamp): End index of the gap.
    - "start_inclusive" (Boolean):
    - "end_inclusive" (Boolean):
    - "gap_size" (Timedelta): Size of the gap
    - "value_to_left" (Float/Int): If existing, last value before the gap, otherwise None
    - "value_to_right" (Float/Int): If existing, first value after the gap, otherwise None
    - "mean_left_right" (Float/Int): The mean value of the `value_to_left` and `value_to_right`.
      None, if at least one of these values is None.

## Details

The component follows these steps:
2. Constrict the timeseries to start_date and end_date, if defined.
3. Ensure that start_date and end_date are present in the constricted timeseries.
4. Detect gaps in the timeseries and determine their boundaries.
If the `start_date` (`end_date`) is defined, the component checks that it is present in the
`series` and removes any data points with an earlier (later) index from the processing range.
To detect gaps the time steps between consecutive data points are calculated. If `auto_stepsize` is
set to `True` the component determines the `step_size`
 When a time step is
larger than the product of the `step_size_factor` and the step size defined by `step_size`, it
is considered to be a gap.
"""


from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, validator

from hetdesrun.runtime.exceptions import ComponentInputValidationException


class GapDetectionParameters(BaseModel):
    start_date: pd.Timestamp | None  # pydantic kann auch direkt datetime, muss aber getestet werden
    end_date: pd.Timestamp | None
    auto_stepsize: bool
    history_end_date: pd.Timestamp | None
    step_size_str: str
    percentil: float
    step_size_factor: float
    min_amount_datapoints: int
    interpolation_method: str
    fill_value: Any

    @validator("end_date")
    def verify_dates(cls, end_date, values: dict):
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
    def verify_history_end_date(cls, history_end_date, values: dict) -> datetime | None:
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

    @validator("step_size_str")
    def verify_step_size(cls, step_size, values: dict) -> str:
        auto_stepsize = values["auto_stepsize"]
        if auto_stepsize is False:
            if step_size is None:
                raise ComponentInputValidationException(
                    "A step_size is required for gap detection, "
                    "if it is not automatically determined.",
                    error_code=422,
                    invalid_component_inputs=["step_size_str"],
                )
            try:
                try:
                    _ = pd.to_timedelta(step_size)
                except ValueError:
                    _ = pd.to_timedelta(pd.tseries.frequencies.to_offset(step_size))
            except ValueError as err:
                raise ComponentInputValidationException(
                    "A step_size is required for gap detection, "
                    "if it is not automatically determined.",
                    error_code=422,
                    invalid_component_inputs=["step_size_str"],
                ) from err
        return step_size

    @validator("percentil")
    def verify_percentile(cls, percentil) -> float:
        if (percentil < 0) or (percentil > 1):
            raise ComponentInputValidationException(
                "The percentil value has to be a non-negative float less or equal to 1.",
                error_code=422,
                invalid_component_inputs=["percentil"],
            )
        return percentil

    @validator("step_size_factor")
    def verify_step_size_factor(cls, factor) -> float:
        if factor < 0:
            raise ComponentInputValidationException(
                "The gap size factor has to be a non-negative float.",
                error_code=422,
                invalid_component_inputs=["step_size_factor"],
            )
        return factor

    @validator("min_amount_datapoints")
    def verify_min_amount_datapoints(cls, min_amount) -> int:
        if min_amount < 0:
            raise ComponentInputValidationException(
                "The minimum amount of datapoints has to be a non-negative integer.",
                error_code=422,
                invalid_component_inputs=["min_amount_datapoints"],
            )
        return min_amount


def timestamp_str_to_pd_timestamp(timestamp: str) -> datetime:
    try:
        date = pd.to_datetime(timestamp, utc=True)
    except ValueError as error:
        raise ComponentInputValidationException(
            str(error), error_code=422, invalid_component_inputs=["..."]
        ) from error
    return date


def freqstr2dateoffset(freqstr: str) -> pd.DateOffset:
    """Transform frequency string to Pandas DateOffset."""
    return pd.tseries.frequencies.to_offset(freqstr)


def freqstr2timedelta(freqstr: str) -> pd.Timedelta:
    """Transform frequency string to Pandas Timedelta."""
    try:
        return pd.to_timedelta(freqstr)
    except ValueError:
        return pd.to_timedelta(freqstr2dateoffset(freqstr))


def check_add_boundary_dates(
    timeseries: pd.Series, start_date: datetime, end_date: datetime, fill_value=None
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


def check_amount_datapoints(series: pd.Series, min_amount_datapoints: int):
    if len(series) < min_amount_datapoints:
        raise ComponentInputValidationException(
            f"The timeseries must contain at least {min_amount_datapoints} datapoints.",
            error_code=422,
            invalid_component_inputs=["timeseries"],
        )


def determine_timestep_gapsize_percentile(
    timeseries_data: pd.Series | pd.DataFrame,
    percentil: float,
    interpolation_method: str,
) -> pd.Timedelta:
    gaps = timeseries_data.index.to_series().diff().dropna()

    percentile_gapsize = gaps.quantile(percentil, interpolation=interpolation_method)

    return percentile_gapsize


def determine_gap_length(
    timeseries: pd.Series, stepsize=timedelta(minutes=1)
) -> pd.DataFrame:
    gaps = timeseries.index.to_series().diff().to_numpy()

    stepsize_seconds = stepsize.total_seconds()

    normalized_gaps = [
        pd.Timedelta(gap).total_seconds() / stepsize_seconds if pd.notna(gap) else None
        for gap in gaps
    ]

    result_df = pd.DataFrame(
        {"value": timeseries.to_numpy(), "gap": normalized_gaps}, index=timeseries.index
    )

    return result_df


def return_gap_boundary_timestamps(
    frame_with_gapsizes: pd.DataFrame, series: pd.Series, step_size_factor=1.0
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
        "auto_stepsize": {"data_type": "BOOLEAN"},
        "history_end_date_str": {"data_type": "STRING", "default_value": None},
        "percentil": {"data_type": "FLOAT", "default_value": 0.5},
        "interpolation_method": {"data_type": "STRING", "default_value": "nearest"},
        "step_size_str": {"data_type": "STRING", "default_value": None},
        "step_size_factor": {"data_type": "FLOAT", "default_value": 1.0},
        "fill_value": {"data_type": "ANY", "default_value": None},
        "min_amount_datapoints": {"data_type": "INT", "default_value": 21},
    },
    "outputs": {
        "gap_info": {"data_type": "DATAFRAME"},
    },
    "name": "Gap Detection Intervals",
    "category": "Data Quality",
    "description": "Detects gaps in the given series that are larger than the step size and returns a DataFrame with information about the gaps.",  # noqa: E501
    "version_tag": "1.0.0",
    "id": "58c5b077-13b2-4e0d-8882-c5526d9d55a6",
    "revision_group_id": "e3efbd08-9d0e-45c4-8330-01f3b856a6e6",
    "state": "DRAFT",
}


def main(
    *,
    timeseries,
    auto_stepsize,
    step_size_str=None,
    start_date_str=None,
    end_date_str=None,
    step_size_factor=1,
    fill_value=None,
    percentil=0.5,
    history_end_date_str=None,
    min_amount_datapoints=21,
    interpolation_method="nearest",
):
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

    if step_size_str is None and "ref_frequency" in timeseries.attrs:
        step_size_str = timeseries.attrs["ref_frequency"]

    start_date = timestamp_str_to_pd_timestamp(start_date_str)
    end_date = timestamp_str_to_pd_timestamp(end_date_str)
    history_end_date = timestamp_str_to_pd_timestamp(history_end_date_str)

    input_params = GapDetectionParameters(
        start_date=start_date,
        end_date=end_date,
        auto_stepsize=auto_stepsize,
        history_end_date_str=history_end_date,
        step_size_str=step_size_str,
        percentil=percentil,
        min_amount_datapoints=min_amount_datapoints,
        interpolation_method=interpolation_method,
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
        step_size = determine_timestep_gapsize_percentile(
            training_series, percentil, interpolation_method
        )
    else:
        step_size = freqstr2timedelta(step_size_str)

    df_with_gaps = determine_gap_length(constricted_series, step_size)

    return {
        "gap_info": return_gap_boundary_timestamps(
            df_with_gaps, constricted_series, step_size_factor
        )
    }
