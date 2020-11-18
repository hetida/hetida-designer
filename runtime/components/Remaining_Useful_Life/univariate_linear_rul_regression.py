from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import datetime
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression


def rul_regression_linear(
    train_series: pd.Series,
    limit: float,
    num_pred_series_future_days: int,
    pred_series_frequency: str = "min",
):
    """Linear Regression for univariate Remaining Useful Life (RUL) prediction
    
    train-series: pd.Series with datetime index and float values. The input data to train
        the regression model.
    limit: the limit value against which rul should be made.
    
    returns: Tuple (pred_y, timestamp_limit_reached, intercept, slope)
    """

    train_x_vals = pd.Series(train_series.index, index=train_series.index)

    min_timestamp, max_timestamp = train_x_vals.min(), train_x_vals.max()

    train_x_diffs = (
        train_x_vals - min_timestamp
    )  # time_deltas to chronologically first timestamp

    lg = LinearRegression()
    lg.fit(
        train_x_diffs.dt.total_seconds().values.reshape(-1, 1),
        train_series.values.reshape(-1, 1),
    )
    intercept, slope = lg.intercept_[0], lg.coef_[0]

    max_timestamp_preds = max_timestamp + datetime.timedelta(
        days=num_pred_series_future_days
    )
    pred_x_vals = pd.date_range(
        start=min_timestamp, end=max_timestamp_preds, freq=pred_series_frequency
    )
    pred_x_diffs = pd.Series(pred_x_vals - min_timestamp)
    pred_y = pd.Series(
        lg.predict(pred_x_diffs.dt.total_seconds().values.reshape(-1, 1)).reshape(
            1, -1
        )[0],
        index=pred_x_vals,
    )

    if slope == 0:
        limit_reached_secs_from_min_timestamp = None
    else:

        limit_reached_secs_from_min_timestamp = ((limit - intercept) / slope)[0]

    if limit_reached_secs_from_min_timestamp is not None:
        timestamp_limit_reached = min_timestamp + datetime.timedelta(
            seconds=limit_reached_secs_from_min_timestamp
        )
    else:
        timestamp_limit_reached = pd.NaT
    return pred_y, timestamp_limit_reached, intercept, slope


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={
        "num_pred_series_future_days": DataType.Integer,
        "pred_series_frequency": DataType.String,
        "timeseries": DataType.Series,
        "limit": DataType.Float,
    },
    outputs={
        "intercept": DataType.Float,
        "limit_violation_prediction_timestamp": DataType.String,
        "pred_series": DataType.Series,
        "slope": DataType.Float,
    },
)
def main(*, num_pred_series_future_days, pred_series_frequency, timeseries, limit):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    pred_y, timestamp_limit_reached, intercept, slope = rul_regression_linear(
        timeseries, limit, num_pred_series_future_days, pred_series_frequency
    )
    return {
        "pred_series": pred_y,
        "intercept": intercept,
        "slope": slope,
        "limit_violation_prediction_timestamp": timestamp_limit_reached.to_pydatetime().isoformat()
        if timestamp_limit_reached != pd.NaT
        else None,
    }
