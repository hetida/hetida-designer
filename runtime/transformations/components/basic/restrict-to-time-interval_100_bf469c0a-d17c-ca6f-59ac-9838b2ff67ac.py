"""Documentation for Restrict to time interval

# Restrict to time interval

## Description
This component restricts a Pandas Series or Pandas DataFrame to a Pandas Series or Pandas DataFrame with respect to some given time interval.

## Inputs
* **data** (Pandas Series or Pandas DataFrame): Indices must be datetimes, either without timezone name or with utc offset.
* **start** (String): Date as popular format (e.g. "10 Aug 2012 10:20:30", "2019-08-01T15:20:10") or relative dates (e.g. "yesterday -10 years", "1 hour ago -0500"), either without timezone name or with utc offset.
* **stop** (String): Date as popular format (e.g. "10 Aug 2012 10:20:30", "2019-08-01T15:20:10") or relative dates (e.g. "yesterday -10 years", "1 hour ago -0500"), either without timezone name or with utc offset.

## Outputs
* **interval** (Pandas Series or Pandas DataFrame): Contains data restricted to the indices between start and stop.

## Details
The component restricts the input data to the time interval between start and stop. Entries with index before start or after stop are filtered.

## Examples
The json input of a typical call of this component with a Pandas Series without timezone is
```
{
        "data": {
                                "2019-08-01T15:20:10": 3.3,
                                "2019-08-01T15:20:20": 7.5,
                                "2019-08-01T15:20:25": 0.3,
                                "2019-08-01T15:20:30": 0.5
        },
        "start": "2019-08-01T15:20:15",
        "stop": "2020-08-01T15:20:30"
}
```
The expected output is
```
        "interval": {
                                "2019-08-01T15:20:20": 7.5,
                                "2019-08-01T15:20:25": 0.3,
                                "2019-08-01T15:20:30": 0.5
                }
```

The json input of a typical call of this component with a Pandas Series without utc offset is
```
{
        "data": {
                                "2016-12-31 00:30:00+01:00": 3.3,
                                "2016-12-31 00:30:10+01:00": 7.5,
                                "2016-12-31 00:30:20+01:00": 0.3,
                                "2016-12-31 00:30:30+01:00": 0.5
        },
        "start": "2016-12-31 00:30:10+01:00",
        "stop": "2016-12-31 00:30:20+01:00"
}
```
The expected output is
```
        "interval": {
                                "2016-12-31 00:30:10+00:00": 7.5,
                                "2016-12-31 00:30:20+00:00": 0.3
                }
```
"""

from datetime import datetime, timezone

import dateparser
import pandas as pd


def parse_to_utc(datetime_string: str, enforce_aware: bool = True) -> datetime:
    """
    Parse a datetime string to UTC datetime, preferring ISO format first
    and ensuring that the result is explicitly UTC.

    Naive timestamps are interpreted as UTC and aware timestamps are
    transformed to UTC.

    This uses dateparser if parsing using datetime.fromisoformat fails.

    Args:
        datetime_string (str): The datetime string to parse
        enforce_aware (bool): Whether the result should be enforced to be an aware timestamp.
            Activating this interprets unaware timestamps as UTC.

    Returns:
        datetime: A timezone-aware datetime object in UTC

    Raises:
        ValueError: If the string cannot be parsed
    """
    if not isinstance(datetime_string, str):
        raise ValueError("Input must be a string")

    # First, try parsing as ISO format using datetime.fromisoformat
    try:
        dt = datetime.fromisoformat(datetime_string)

        if enforce_aware and dt.tzinfo is None:  # If naive, assume UTC
            return dt.replace(tzinfo=timezone.utc)

        if dt.tzinfo is not None:
            # If aware, convert to UTC
            return dt.astimezone(timezone.utc)

        return dt

    except ValueError:
        # If ISO format fails, fall back to dateparser
        try:
            # Configure dateparser to interpret relative dates in UTC
            dt = dateparser.parse(
                datetime_string, settings={"TIMEZONE": "UTC", "TO_TIMEZONE": "UTC"}
            )

            if dt is None:
                raise ValueError(f"Could not parse datetime string: '{datetime_string}'")

            if (
                enforce_aware and dt.tzinfo is None
            ):  # If naive, assume UTC (should already be UTC due to settings)
                return dt.replace(tzinfo=timezone.utc)

            if dt.tzinfo is not None:
                # If aware, convert to UTC
                return dt.astimezone(timezone.utc)

            return dt

        except Exception as e:
            raise ValueError(f"Could not parse datetime string: '{datetime_string}'") from e


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "data": {"data_type": "ANY"},
        "start": {"data_type": "STRING"},
        "stop": {"data_type": "STRING"},
    },
    "outputs": {
        "interval": {"data_type": "ANY"},
    },
    "name": "Restrict to time interval",
    "category": "Basic",
    "description": "Returns the data belonging to some time interval",
    "version_tag": "1.0.0",
    "id": "bf469c0a-d17c-ca6f-59ac-9838b2ff67ac",
    "revision_group_id": "bf469c0a-d17c-ca6f-59ac-9838b2ff67ac",
    "state": "RELEASED",
    "released_timestamp": "2022-02-09T17:33:28.749503+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, data, start, stop):
    # entrypoint function for this component
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
                parsed_start_date = parse_to_utc(start, enforce_aware=False)
            else:
                parsed_start_date = parse_to_utc(start, enforce_aware=True)
        except (ValueError, TypeError, AttributeError) as e:
            raise ValueError(f"start timestamp could not be parsed: {start}") from e
        if parsed_start_date is None:
            raise ValueError(f"start timestamp could not be parsed: {start}")
    else:
        parsed_start_date = None

    if stop is not None:
        try:
            if data.index.tzinfo is None:
                parsed_stop_date = parse_to_utc(stop, enforce_aware=False)
            else:
                parsed_stop_date = parse_to_utc(stop, enforce_aware=True)
        except (ValueError, TypeError) as e:
            raise ValueError(f"stop timestamp could not be parsed: {stop}") from e
        if parsed_stop_date is None:
            raise ValueError(f"stop timestamp could not be parsed: {stop}")
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
    if parsed_start_date is None and parsed_stop_date is not None:
        return {"interval": data.loc[:parsed_stop_date]}
    if parsed_start_date is not None and parsed_stop_date is None:
        return {"interval": data.loc[parsed_start_date:]}
    return {"interval": data}


TEST_WIRING_FROM_PY_FILE_IMPORT = {}
RELEASE_WIRING = {}
