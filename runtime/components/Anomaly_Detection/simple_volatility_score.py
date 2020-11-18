from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType


def volatility(series, freq, stamped="right"):
    """A simple volatility measurement
    
    Tries to measure volatility in a time series. Works by comparing sum of absolute
    differences to the absolute value of the sum of differences on moving windows.
    
    series: (Pandas.Series): Should have a datetime index and float values. The series of
        which volatility is measured.
    freq (String): Something like "2h" or "75min". Determines the rolling window size.
    stamped (String): One of "left" or "right" or "center". Determines whether the resulting volatility
        Series is timestamped left or right of the intervals. "center" only works if freq
        is explicitely divisible by 2 (i.e. freq is something like "2h" or "4min"). You can make
        center work on a frequency of "1h" by switching to "60min" instead!
    
    Returns: A series of volatility "scores"
    """
    diffs = series.sort_index().diff(1)

    vols = diffs.abs().rolling(freq).sum() - diffs.rolling(freq).sum().abs()
    vols.name = "volatilities"

    if stamped == "left":
        return vols.shift(freq=freq, periods=-1)
    elif stamped == "right":
        return vols
    elif stamped == "center":
        return vols.shift(
            freq=freq, periods=-0.5
        )  # only works if freq is "divisible by 2"
    else:
        raise ValueError(
            "Only 'left' or 'right' or 'center' allowed for stamping parameter."
        )


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={
        "timeseries": DataType.Series,
        "window_size": DataType.String,
        "window_timestamp_location": DataType.String,
    },
    outputs={"volatilities": DataType.Series},
)
def main(*, timeseries, window_size, window_timestamp_location):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {
        "volatilities": volatility(timeseries, window_size, window_timestamp_location)
    }
