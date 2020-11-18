from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import pandas as pd
import numpy as np
import dateparser
import pytz
from pandas._libs.tslibs import OutOfBoundsDatetime, Timestamp

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"data": DataType.Any, "start": DataType.String, "stop": DataType.String},
    outputs={"interval": DataType.Any},
)
def main(*, data, start, stop):
    """entrypoint function for this component

    Usage example:
    >>> main(
    ...     data = pd.Series(
    ...        {
    ...            "2019-08-01T15:20:10": 1.7,
    ...            "2019-08-01T15:20:20": 27.0,
    ...            "2019-08-01T15:20:25": 0.3,
    ...            "2019-08-01T15:20:30": 0.5,
    ...        }
    ...     ),
    ...     start = "2019-08-01T15:20:12", 
    ...     stop = "2019-12-01T15:23:00"   
    ...     )["interval"]
    2019-08-01 15:20:20    27.0
    2019-08-01 15:20:25     0.3
    2019-08-01 15:20:30     0.5
    dtype: float64
    """
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    if data.empty:
        return {"interval": data}

    try:
        data.index = pd.to_datetime(data.index)
    except ValueError:
        data.index = pd.to_datetime(data.index, utc=True)

    data = data.sort_index()

    if start is not None:
        try:
            if data.index.tzinfo is None:
                parsed_start_date = dateparser.parse(
                    start,
                    settings={"TIMEZONE": "UTC", "RETURN_AS_TIMEZONE_AWARE": False},
                )
            else:
                parsed_start_date = dateparser.parse(
                    start,
                    settings={"TIMEZONE": "UTC", "RETURN_AS_TIMEZONE_AWARE": True},
                ).replace(tzinfo=pytz.UTC)
        except (ValueError, TypeError, AttributeError):
            raise ValueError(f"start timestamp could not be parsed: {start}")
        if parsed_start_date is None:
            raise ValueError(f"start timestamp could not be parsed: {start}")
    else:
        parsed_start_date = None

    if stop is not None:
        try:
            if data.index.tzinfo is None:
                parsed_stop_date = dateparser.parse(
                    stop,
                    settings={"TIMEZONE": "UTC", "RETURN_AS_TIMEZONE_AWARE": False},
                )
            else:
                parsed_stop_date = dateparser.parse(
                    stop, settings={"TIMEZONE": "UTC", "RETURN_AS_TIMEZONE_AWARE": True}
                ).replace(tzinfo=pytz.UTC)
        except (ValueError, TypeError):
            raise ValueError(f"stop timestamp could not be parsed: {stop}")
        if parsed_stop_date is None:
            raise ValueError(f"start timestamp could not be parsed: {start}")
    else:
        parsed_stop_date = None

    if (
        (parsed_start_date is not None)
        and (parsed_stop_date is not None)
        and (parsed_start_date > parsed_stop_date)
    ):
        raise ValueError("start timestamp cannot be after stop timestamp")

    if parsed_start_date is not None and parsed_stop_date is not None:
        return {"interval": data.loc[parsed_start_date:parsed_stop_date]}
    elif parsed_start_date is None and parsed_stop_date is not None:
        return {"interval": data.loc[:parsed_stop_date]}
    elif parsed_start_date is not None and parsed_stop_date is None:
        return {"interval": data.loc[parsed_start_date:]}
    else:
        return {"interval": data}
