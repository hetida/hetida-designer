import datetime

import pandas as pd
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
        train_x_diffs.dt.total_seconds().to_numpy().reshape(-1, 1),
        train_series.to_numpy().reshape(-1, 1),
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
        lg.predict(pred_x_diffs.dt.total_seconds().to_numpy().reshape(-1, 1)).reshape(
            1, -1
        )[0],
        index=pred_x_vals,
    )

    limit_reached_secs_from_min_timestamp = (
        ((limit - intercept) / slope)[0] if slope != 0 else None
    )

    if limit_reached_secs_from_min_timestamp is not None:
        timestamp_limit_reached = min_timestamp + datetime.timedelta(
            seconds=limit_reached_secs_from_min_timestamp
        )
    else:
        timestamp_limit_reached = pd.NaT
    return pred_y, timestamp_limit_reached, intercept, slope


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "num_pred_series_future_days": {"data_type": "INT", "default_value": 3},
        "pred_series_frequency": {"data_type": "STRING", "default_value": "5min"},
        "timeseries": {"data_type": "SERIES"},
        "limit": {"data_type": "FLOAT"},
    },
    "outputs": {
        "intercept": {"data_type": "FLOAT"},
        "slope": {"data_type": "FLOAT"},
        "pred_series": {"data_type": "SERIES"},
        "limit_violation_prediction_timestamp": {"data_type": "STRING"},
    },
    "name": "Univariate Linear RUL Regression",
    "category": "Remaining Useful Life",
    "description": "Linear Regression for Remaining Useful Life on univariate timeseries",
    "version_tag": "1.1.0 Copy",
    "id": "e8ab3aa4-103c-4515-b690-8fd07e294711",
    "revision_group_id": "6c73f83b-19f0-4caf-b97b-a25e21b93ed5",
    "state": "DRAFT",
}


def main(
    *, timeseries, limit, num_pred_series_future_days=3, pred_series_frequency="5min"
):
    # entrypoint function for this component
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
