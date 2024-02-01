"""Documentation for component "Gap Intervals to Replacement Positions"

# Gap Intervals to Replacement Positions

## Description


## Inputs
- **timeseries** (Series):
  Expects a series with an index of data type DateTimeIndex.

- **start_date_str** (String, default value: null):
  Desired start date of the processing range. Expexcts ISO 8601 format. Alternatively, the
  `timeseries` can have an attribute "start_date" that will be used instead. If neither is
  defined, the processing range begins with the first data point in `timeseries`. The start date
  must not be later than the end date.

- **end_date_str** (String, default value: null):
  Desired end date of the processing range. Expexcts ISO 8601 format. Alternatively, the
  `timeseries` can have an attribute "end_date" that will be used instead. If neither is defined,
  the processing range ends with the last data point in `timeseries`. The start date must not be
  later than the end date.

- **data_frequency** (String): Time span between data points. Can be either a Pandas frequency
  string based on [date offset aliases](
    https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#timeseries-offset-aliases
  ) or a timedelta string.

- **frequency_offset** (String): Offset of the window starts compared to 1970-01-01 00:00:00.
  Can be either a Pandas frequency string based on [date offset aliases](
    https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#timeseries-offset-aliases
  ) or a timedelta string.
  In most cases no offset is necessary, so this can be set to zero, i.e. "0".

- **gaps** (DataFrame) :
  A DataFrame containing the beginning and end timestamps of gaps larger than the determined or
  given step size. Index is of type DateTimeIndex.
  Required columns are:
  - "start" (Timestamp): Start index of the gap.
  - "end"(Timestamp): End index of the gap.
  - "gap": Size of the gap relative to the stepsize
  - "start_inclusive" (Boolean):
  - "end_inclusive" (Boolean)

## Outputs
- **replacement_value_locations** (Series):

## Details

"""

import pandas as pd


def freqstr2dateoffset(freqstr: str) -> pd.DateOffset:
    """Transform frequency string to Pandas DateOffset."""
    return pd.tseries.frequencies.to_offset(freqstr)


def freqstr2timedelta(freqstr: str) -> pd.Timedelta:
    """Transform frequency string to Pandas Timedelta."""
    try:
        return pd.to_timedelta(freqstr)
    except ValueError:
        return pd.to_timedelta(freqstr2dateoffset(freqstr))
