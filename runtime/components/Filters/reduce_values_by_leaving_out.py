"""Reduce data set by leaving out values

# Reduce data by leaving out values

This is mainly used in preprocessing extensive datasets for more performant plotting

Notes:
* this simply takes every n'th datapoint for a suitable n if some preconditions hold
* n is computed via round((len(data) - 1) / (number_of_points - 1)) meaning
    * at the end you can still have more than given number_of_points datapoints!
    * while the first datapoint is always included, the last one is not necessarily included

WARNING: This is by no means an analytically reasonable way to reduce the number
of data points! A more sophisticated method should be used which uses statistical
distribution of data points in order to keep relevant outliers etc.
"""

from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType


MIN_NUMBER_POINTS = 2


def reduce_data(data, number_of_points: int):
    """Reduce number of data points for performant plots"""
    if (len(data) >= number_of_points) and (number_of_points >= MIN_NUMBER_POINTS):
        return data.iloc[:: int(round((len(data) - 1) / (number_of_points - 1)))]
    return data.iloc[::1].copy()


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"data": DataType.Any, "number_of_points": DataType.Integer},
    outputs={"data": DataType.Any},
)
def main(*, data, number_of_points):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {"data": reduce_data(data, number_of_points)}
