from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import datetime
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression


def regression_linear(xs, ys):
    """Linear Regression"""

    lg = LinearRegression()
    lg.fit(xs, ys)
    intercept, slope = lg.intercept_, lg.coef_

    preds = pd.DataFrame(lg.predict(xs), columns=ys.columns, index=xs.index)

    diffs = preds - ys
    slope_df = pd.DataFrame(slope)
    slope_df = slope_df.transpose()
    slope_df.columns = ys.columns
    slope_df.index = xs.columns

    return preds, diffs, pd.Series(intercept, index=ys.columns), slope_df, lg


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"x_values": DataType.DataFrame, "y_values": DataType.DataFrame},
    outputs={
        "diffs": DataType.DataFrame,
        "intercept": DataType.Series,
        "preds": DataType.DataFrame,
        "slope": DataType.DataFrame,
        "trained_model": DataType.Any,
    },
)
def main(*, x_values, y_values):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    preds, diffs, intercept, slope, trained_model = regression_linear(
        x_values, y_values
    )
    return {
        "diffs": diffs,
        "intercept": intercept,
        "slope": slope,
        "preds": preds,
        "trained_model": trained_model,
    }
