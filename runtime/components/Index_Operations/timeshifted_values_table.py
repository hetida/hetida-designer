from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType  # add your own imports here

import pandas as pd


def past_values(series: pd.Series, periods, frequency) -> pd.DataFrame():
    df = pd.DataFrame()

    sign = -1 if periods < 0 else 1

    for n in range(sign * periods):
        shift_no = sign * (n + 1)
        df["shifted_" + str(shift_no) + "_times_" + frequency] = series.shift(
            periods=shift_no, freq=frequency
        )
    return df


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={
        "timeseries": DataType.Series,
        "freq": DataType.String,
        "periods": DataType.Integer,
    },
    outputs={"timeshifted_values": DataType.DataFrame},
)
def main(*, timeseries, freq, periods):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    return {"timeshifted_values": past_values(timeseries, periods, freq)}

