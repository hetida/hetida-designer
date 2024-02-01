"""Documentation for component "Gap Intervals to Replacement Positions"

# Gap Intervals to Replacement Positions

## Description


## Inputs
- **timeseries** (Series):
  Expects a series with an index of data type DateTimeIndex.
* **data_frequency** (String): Time span between data points. Can be either a Pandas frequency
  string based on [date offset aliases](
    https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#timeseries-offset-aliases
  ) or a timedelta string.
* **frequency_offset** (String): Offset of the window starts compared to 1970-01-01 00:00:00.
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

