"""Documentation for component "Gap Detection Intervals"

# Gap Detection Intervals

## Description
Detects gaps in the given series that are larger than the step size and returns a DataFrame with
information about the gaps.

## Inputs
- **timeseries** (Pandas Series):
    Expects datetime index.

- **start_date_str** (String):
    Desired start date of the processing range. Expexcts iso format. Alternatively the `timeseries`
    can have a attribute "start_date" that will be used instead. If neither is defined, the
    processing range begins with the first data point in `timeseries`.

- **end_date_str** (String):
    Desired end date of the processing range. Expexcts iso format. Alternatively the `timeseries`
    can have a attribute "end_date" that will be used instead. If neither is defined, the
    processing range ends with the last data point in `timeseries`.

**step_size** (String):
    The expected time step unit between consecutive timestamps in the time series.

**step_size_factor** (Float):
    Expects value >= 0. The value is used to define when a step between two consecutive data points
    is recognized as a gap. I.e. a value of 1.0 means that all steps larger than the specified
    `step_size` are recognized as gaps, while a value of 2.0 means that steps are only recognized as
    gaps if they are more than twice as large as the specified `step_size`.


## Outputs
**gap_boundaries** (Pandas DataFrame) :
    A DataFrame containing the beginning and end timestamps of gaps larger than the determined or
    given step size.
    Columns are:
    - "start" (Timestamp): Start index of the gap.
    - "end"(Timestamp): End index of the gap.
    - "start_inclusive" (Boolean):
    - "end_inclusive" (Boolean):
    - "gap_size": Size of the gap
    - "value_to_left": If existing, last value before the gap, otherwise None
    - "value_to_right": If existing, first value after the gap, otherwise None
    - "mean_left_right": The mean value of the `value_to_left` and `value_to_right`, None, if at
    least one of these values is None

## Raises

ComponentInputValidationException:
    - If start_date is greater than end_date.

## Details

The function follows these steps:
1. Validate input.
2. Constrict the timeseries to start_date and end_date, where defined.
3. Ensure that start_date and end_date are present in the constricted timeseries.
4. Detect gaps in the timeseries and determine their boundaries.
"""


import contextlib
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, validator

from hetdesrun.runtime.exceptions import ComponentInputValidationException


class GapDetectionParameters(BaseModel):
    start_date: pd.Timestamp | None
    end_date: pd.Timestamp | None
    step_size_str: str
    step_size_factor: float = 1.0
    fill_value: Any = None

    # TODO was ist mit dem Fall Attribut der Zeitreihe?

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

    @validator("step_size_factor")
    def verify_step_size_factor(cls, factor) -> float:
        if factor < 0:
            raise ComponentInputValidationException(
                "The gap size factor has to be a non-negative float less or equal to 1.",  # TODO Fehlermeldung anpassen
                error_code=422,
                invalid_component_inputs=["step_size_factor"],
            )
        return factor


def timestamp_str_to_pd_timestamp(timestamp: str) -> datetime:
    try:
        date = pd.to_datetime(timestamp, utc=True)
    except ValueError as error:
        raise ComponentInputValidationException(
            str(error), error_code=422, invalid_component_inputs=["..."]
        ) from error
    return date


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


def determine_gap_length(
    timeseries: pd.Series, stepsize=timedelta(minutes=1)
) -> pd.DataFrame:
    gaps = timeseries.index.to_series().diff().to_numpy()

    stepsize_seconds = stepsize.total_seconds()

    normalized_gaps = [
        pd.Timedelta(gap).total_seconds() / stepsize_seconds if pd.notna(gap) else None
        for gap in gaps
    ]  # TODO in Doku erklären was eine Gap sein soll

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
            "mean_left_right": (left_values + right_values) / 2,
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
        "step_size_str": {"data_type": "STRING"},
        "step_size_factor": {"data_type": "FLOAT", "default_value": 1.0},
        "fill_value": {"data_type": "ANY", "default_value": None},
    },
    "outputs": {},
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
    step_size_str,
    start_date_str=None,
    end_date_str=None,
    step_size_factor=1.0,
    fill_value=None,
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    timeseries = timeseries.sort_index().dropna()

    start_date = timestamp_str_to_pd_timestamp(start_date_str)
    end_date = timestamp_str_to_pd_timestamp(end_date_str)

    input_params = GapDetectionParameters(
        start_date=start_date,
        end_date=end_date,
        step_size_str=step_size_str,
        fill_value=fill_value,
    )
    constricted_series = constrict_series_to_dates(
        timeseries, input_params.start_date, input_params.end_date
    )

    step_size = freqstr2timedelta(step_size_str)
    series_with_bounds = check_add_boundary_dates(
        constricted_series, input_params.start_date, input_params.end_date
    )

    df_with_gaps = determine_gap_length(series_with_bounds, step_size)

    return return_gap_boundary_timestamps(
        df_with_gaps, series_with_bounds, step_size_factor
    )
