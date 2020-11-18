from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import datetime
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression


def regression_linear(xs: pd.Series, ys: pd.Series):
    """Linear Regression for univariate Remaining Useful Life (RUL) prediction
    
    train-series: pd.Series with datetime index and float values. The input data to train
        the regression model.
    limit: the limit value against which rul should be made.
    
    returns: Tuple (pred_y, timestamp_limit_reached, intercept, slope)
    """

    lg = LinearRegression()
    lg.fit(xs.values.reshape(-1, 1), ys.values.reshape(-1, 1))
    intercept, slope = lg.intercept_[0], lg.coef_[0]

    preds = pd.Series(
        lg.predict(xs.values.reshape(-1, 1)).reshape(1, -1)[0], index=xs.index
    )

    diffs = preds - ys

    return preds, diffs, intercept, slope


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"x_values": DataType.Series, "y_values": DataType.Series},
    outputs={
        "diffs": DataType.Series,
        "intercept": DataType.Float,
        "slope": DataType.Float,
        "preds": DataType.Series,
    },
)
def main(*, x_values, y_values):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    preds, diffs, intercept, slope = regression_linear(x_values, y_values)
    return {"diffs": diffs, "intercept": intercept, "slope": slope, "preds": preds}
