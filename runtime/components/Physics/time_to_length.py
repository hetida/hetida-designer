from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import pandas as pd
from scipy import integrate

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"data": DataType.Series, "speed": DataType.Any},
    outputs={"result": DataType.Series},
)
def main(*, data, speed):
    """entrypoint function for this component
    Usage example:
    >>> main(
    ...     data = pd.Series(
    ...         {
    ...             "2019-08-01T15:20:10": 3.0,
    ...             "2019-08-01T15:20:11": 22.0,
    ...             "2019-08-01T15:20:14": 18.0,
    ...             "2019-08-01T15:20:16": 2.0,
    ...             "2019-08-01T15:20:18": 7.0,
    ...             "2019-08-01T15:20:22": 12.0,
    ...             "2019-08-01T15:20:24": 15.0,
    ...             "2019-08-01T15:20:26": 18.0,
    ...        }
    ...     ),
    ...     speed = 5
    ... )["result"]
    0.0      3.0
    5.0     22.0
    20.0    18.0
    30.0     2.0
    40.0     7.0
    60.0    12.0
    70.0    15.0
    80.0    18.0
    dtype: float64
    >>> main(
    ...     data = pd.Series(
    ...         {
    ...             "2019-08-01T15:20:10": 3.0,
    ...             "2019-08-01T15:20:11": 22.0,
    ...             "2019-08-01T15:20:14": 18.0,
    ...             "2019-08-01T15:20:16": 2.0,
    ...             "2019-08-01T15:20:18": 7.0,
    ...             "2019-08-01T15:20:22": 12.0,
    ...             "2019-08-01T15:20:24": 15.0,
    ...             "2019-08-01T15:20:26": 18.0,
    ...        }
    ...     ),
    ...     speed = pd.Series(
    ...         {
    ...             "2019-08-01T15:20:10": 1.0,
    ...             "2019-08-01T15:20:11": 3.0,
    ...             "2019-08-01T15:20:14": 4.0,
    ...             "2019-08-01T15:20:16": 2.0,
    ...             "2019-08-01T15:20:18": 0.0,
    ...             "2019-08-01T15:20:22": 2.0,
    ...             "2019-08-01T15:20:24": 4.0,
    ...             "2019-08-01T15:20:26": 5.0,
    ...         }
    ...     )
    ... )["result"]
    0.0      3.0
    2.0     22.0
    12.5    18.0
    18.5     2.0
    20.5     7.0
    24.5    12.0
    30.5    15.0
    39.5    18.0
    dtype: float64
    """
    # ***** DO NOT EDIT LINES ABOVE *****

    data_sort = data.copy()
    try:
        data_sort.index = pd.to_datetime(data_sort.index)
    except (ValueError, TypeError):
        raise TypeError("indices of data must be datetime")

    if isinstance(speed, (int, float, bool)):
        data_sort = data_sort.sort_index()
        time_norm = (data_sort.index - data_sort.index[0]).total_seconds()
        length = pd.Series(speed * time_norm, index=data_sort.index)
    else:
        speed_sort = speed.copy()
        try:
            speed_sort.index = pd.to_datetime(speed_sort.index)
        except (ValueError, TypeError):
            raise TypeError("indices of speed must be datetime")
        speed_sort = speed_sort.sort_index()
        time_norm = (speed_sort.index - speed_sort.index[0]).total_seconds()
        length = pd.Series(
            integrate.cumtrapz(speed_sort.values, time_norm, initial=0),
            index=speed_sort.index,
        )

        intersect = length.index.intersection(data_sort.index)
        length = length.reindex(intersect)
        data_sort = data_sort.reindex(intersect)

    return {"result": pd.Series(data_sort.values, index=length.values)}
