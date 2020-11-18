from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType  # add your own imports here

import numpy as np
import pandas as pd

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={
        "x_min": DataType.Float,
        "x_max": DataType.Float,
        "y_min": DataType.Float,
        "y_max": DataType.Float,
        "n": DataType.Integer,
    },
    outputs={
        "x_values": DataType.Series,
        "y_values": DataType.Series,
        "x_indices": DataType.Series,
        "y_indices": DataType.Series,
    },
)
def main(*, x_min, x_max, y_min, y_max, n):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    xs = np.linspace(x_min, x_max, n)
    ys = np.linspace(y_min, y_max, n)
    xx, yy = np.meshgrid(xs, ys)

    return {
        "x_values": pd.Series(xx.ravel(), name="x"),
        "y_values": pd.Series(yy.ravel(), name="y"),
        "x_indices": pd.Series(xs, name="x"),
        "y_indices": pd.Series(ys, name="y"),
    }
