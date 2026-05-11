"""Documentation for Resample Multi Time Series

# Resample Multi Time Series

## Description
Component to bring several time series from one MultiTSFrame onto the same
target time grid.

Use this component when a MultiTSFrame contains several metrics with irregular
or different timestamps and you want to prepare them for a later component such
as `Align and Merge Multi Time Series`.

This component reuses `Resample Time Series` internally. It splits the
MultiTSFrame into one Pandas Series per metric, resamples each metric with the
same settings, and returns one MultiTSFrame again.

## Inputs
- **multitsframe** (Pandas DataFrame / MultiTSFrame):
    The input time series collection in long MultiTSFrame format. It must
    contain the columns `timestamp`, `metric`, and `value`.
    - `timestamp` contains the timestamps.
    - `metric` identifies the individual time series, for example
      `inverter_1` and `inverter_2`.
    - `value` contains the numeric values.
- **target_frequency** (String):
    Target time frequency such as `5min`, `15min`, `1h`, or `1D`.
    Only fixed timedelta-like frequencies are supported.
- **aggregation_method** (String, default value: "mean"):
    Resampling method. Must be one of `mean`, `median`, `min`, `max`, `sum`,
    or `asfreq`.
    - `mean`, `median`, `min`, `max`, `sum`: aggregate values inside each
      target interval per metric.
    - `asfreq`: only place each metric series on the target grid. No
      aggregation and no filling is performed. New timestamps stay `NaN` if no
      original value exists there.
- **label_position** (String, default value: "left"):
    Determines whether interval-based results are labeled with the left or the
    right boundary of the resampling interval. Must be one of `left` or
    `right`.
- **closed** (String, default value: "left"):
    Determines which side of each interval is closed for interval-based
    resampling. Must be one of `left` or `right`.

## Outputs
- **resampled_multitsframe** (Pandas DataFrame / MultiTSFrame):
    The resampled MultiTSFrame with the columns `timestamp`, `metric`, and
    `value`.

## Details
1. The input must be a MultiTSFrame with the columns `timestamp`, `metric`, and
   `value`.
2. The component keeps only these three columns. Additional columns are not
   carried forward because aggregation across intervals would make their
   meaning ambiguous.
3. Each metric is resampled independently with `Resample Time Series` and the
   same settings.
4. Duplicate rows with the same `timestamp` and `metric` are handled by the
   imported `Resample Time Series` component, which merges duplicate timestamps
   by mean before resampling.
5. The output is returned as one MultiTSFrame again.
6. Missing values created by `asfreq` or by empty target intervals are not
   filled. Use `handle_gaps_and_missing_data` afterwards if you need explicit
   gap handling.

## Example
```json
{
  "multitsframe": [
    {"timestamp": "2026-03-01T00:00:00Z", "metric": "inverter_1", "value": 1.0},
    {"timestamp": "2026-03-01T00:05:00Z", "metric": "inverter_1", "value": 2.0},
    {"timestamp": "2026-03-01T00:10:00Z", "metric": "inverter_1", "value": 3.0},
    {"timestamp": "2026-03-01T00:00:00Z", "metric": "inverter_2", "value": 10.0},
    {"timestamp": "2026-03-01T00:05:00Z", "metric": "inverter_2", "value": 20.0},
    {"timestamp": "2026-03-01T00:10:00Z", "metric": "inverter_2", "value": 30.0}
  ],
  "target_frequency": "10min",
  "aggregation_method": "mean",
  "label_position": "left",
  "closed": "left"
}
```

Expected output:
```json
{
  "resampled_multitsframe": [
    {"timestamp": "2026-03-01T00:00:00Z", "metric": "inverter_1", "value": 1.5},
    {"timestamp": "2026-03-01T00:00:00Z", "metric": "inverter_2", "value": 15.0},
    {"timestamp": "2026-03-01T00:10:00Z", "metric": "inverter_1", "value": 3.0},
    {"timestamp": "2026-03-01T00:10:00Z", "metric": "inverter_2", "value": 30.0}
  ]
}
```
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from hdutils import ComponentInputValidationException, parse_default_value
from hetdesrun.component.load import import_comp

resample_time_series = import_comp("8d9180a9-9b95-4390-aeff-8a36f25f5d7b")

AGGREGATION_METHODS = {"mean", "median", "min", "max", "sum", "asfreq"}
LABEL_POSITIONS = {"left", "right"}
CLOSED_OPTIONS = {"left", "right"}
REQUIRED_COLUMNS = {"timestamp", "metric", "value"}


def validate_multitsframe(multitsframe: pd.DataFrame) -> None:
    if not isinstance(multitsframe, pd.DataFrame):
        raise ComponentInputValidationException(
            "multitsframe must be a pandas DataFrame in MultiTSFrame format",
            error_code="422",
            invalid_component_inputs=["multitsframe"],
        )
    if multitsframe.empty:
        raise ComponentInputValidationException(
            "multitsframe must not be empty",
            error_code="422",
            invalid_component_inputs=["multitsframe"],
        )

    missing_columns = REQUIRED_COLUMNS - set(multitsframe.columns)
    if missing_columns:
        raise ComponentInputValidationException(
            f"multitsframe must contain the columns {sorted(REQUIRED_COLUMNS)}",
            error_code="422",
            invalid_component_inputs=["multitsframe"],
        )

    if not pd.api.types.is_datetime64_any_dtype(multitsframe["timestamp"]):
        raise ComponentInputValidationException(
            "multitsframe column 'timestamp' must be datetime",
            error_code="422",
            invalid_component_inputs=["multitsframe"],
        )
    if multitsframe["timestamp"].isna().any():
        raise ComponentInputValidationException(
            "multitsframe column 'timestamp' must not contain missing values",
            error_code="422",
            invalid_component_inputs=["multitsframe"],
        )
    if multitsframe["metric"].isna().any():
        raise ComponentInputValidationException(
            "multitsframe column 'metric' must not contain missing values",
            error_code="422",
            invalid_component_inputs=["multitsframe"],
        )
    if not pd.api.types.is_numeric_dtype(multitsframe["value"]):
        raise ComponentInputValidationException(
            "multitsframe column 'value' must be numeric",
            error_code="422",
            invalid_component_inputs=["multitsframe"],
        )
    if not np.isfinite(multitsframe["value"].dropna().to_numpy(dtype=float)).all():
        raise ComponentInputValidationException(
            "multitsframe column 'value' must not contain inf or -inf values",
            error_code="422",
            invalid_component_inputs=["multitsframe"],
        )
    if multitsframe["value"].dropna().empty:
        raise ComponentInputValidationException(
            "multitsframe column 'value' must contain at least one non-missing numeric value",
            error_code="422",
            invalid_component_inputs=["multitsframe"],
        )


def validate_inputs(
    multitsframe: pd.DataFrame,
    target_frequency: str,
    aggregation_method: str,
    label_position: str,
    closed: str,
) -> None:
    validate_multitsframe(multitsframe)

    if aggregation_method not in AGGREGATION_METHODS:
        raise ComponentInputValidationException(
            f"aggregation_method must be one of {sorted(AGGREGATION_METHODS)}",
            error_code="422",
            invalid_component_inputs=["aggregation_method"],
        )
    if label_position not in LABEL_POSITIONS:
        raise ComponentInputValidationException(
            "label_position must be one of 'left' or 'right'",
            error_code="422",
            invalid_component_inputs=["label_position"],
        )
    if closed not in CLOSED_OPTIONS:
        raise ComponentInputValidationException(
            "closed must be one of 'left' or 'right'",
            error_code="422",
            invalid_component_inputs=["closed"],
        )

    # Let Resample Time Series validate the exact target frequency semantics.
    resample_time_series.validate_inputs(
        pd.Series(
            [1.0, 2.0],
            index=pd.DatetimeIndex(
                [
                    pd.Timestamp("2026-01-01T00:00:00Z"),
                    pd.Timestamp("2026-01-01T00:01:00Z"),
                ]
            ),
        ),
        target_frequency,
        aggregation_method,
        label_position,
        closed,
    )


def prepare_multitsframe(multitsframe: pd.DataFrame) -> pd.DataFrame:
    prepared = multitsframe[["timestamp", "metric", "value"]].copy()
    prepared["metric"] = prepared["metric"].astype(str)
    prepared["value"] = prepared["value"].astype(float)
    return prepared.sort_values(["metric", "timestamp"])


def build_metric_series(prepared: pd.DataFrame) -> dict[str, pd.Series]:
    metric_series = {}
    for metric, metric_frame in prepared.groupby("metric", sort=True):
        metric_series[str(metric)] = pd.Series(
            metric_frame["value"].to_numpy(dtype=float),
            index=pd.DatetimeIndex(metric_frame["timestamp"]),
            name=str(metric),
            dtype=float,
        ).sort_index()
    return metric_series


def resample_metric_series(
    metric_series: dict[str, pd.Series],
    target_frequency: str,
    aggregation_method: str,
    label_position: str,
    closed: str,
) -> pd.DataFrame:
    result_frames = []

    for metric in sorted(metric_series):
        resampled = resample_time_series.main(
            timeseries=metric_series[metric],
            target_frequency=target_frequency,
            aggregation_method=aggregation_method,
            label_position=label_position,
            closed=closed,
        )["resampled_timeseries"]
        result_frames.append(
            pd.DataFrame(
                {
                    "timestamp": resampled.index,
                    "metric": metric,
                    "value": resampled.to_numpy(dtype=float),
                }
            )
        )

    return pd.concat(result_frames, ignore_index=True).sort_values(["timestamp", "metric"])


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "multitsframe": {"data_type": "MULTITSFRAME"},
        "target_frequency": {"data_type": "STRING"},
        "aggregation_method": {"data_type": "STRING", "default_value": "mean"},
        "label_position": {"data_type": "STRING", "default_value": "left"},
        "closed": {"data_type": "STRING", "default_value": "left"},
    },
    "outputs": {
        "resampled_multitsframe": {"data_type": "MULTITSFRAME"},
    },
    "name": "Resample Multi Time Series",
    "category": "Time Series Base Components",
    "description": "Bring several time series from one MultiTSFrame onto the same target time grid.",  # noqa: E501
    "version_tag": "1.0.0",
    "id": "5f26134a-4e2d-4ec7-bbb3-85443c36cb37",
    "revision_group_id": "3fe9e72c-9cb6-47f5-a509-0e420ee4522b",
    "state": "RELEASED",
    "released_timestamp": "2026-05-11T06:00:00+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(
    *,
    multitsframe,
    target_frequency,
    aggregation_method="mean",
    label_position="left",
    closed="left",
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # Step 1: Validate inputs.
    validate_inputs(
        multitsframe,
        target_frequency,
        aggregation_method,
        label_position,
        closed,
    )

    # Step 2: Keep the MultiTSFrame columns needed for resampling.
    prepared = prepare_multitsframe(multitsframe)

    # Step 3: Split the MultiTSFrame into one Series per metric.
    metric_series = build_metric_series(prepared)

    # Step 4: Resample each metric with Resample Time Series and combine the results.
    resampled = resample_metric_series(
        metric_series,
        target_frequency,
        aggregation_method,
        label_position,
        closed,
    )

    # Step 5: Return the resampled MultiTSFrame.
    return {
        "resampled_multitsframe": resampled,
    }


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "multitsframe",
            "filters": {
                "value": '[\n  {"timestamp": "2026-03-01T00:00:00Z", "metric": "inverter_1", "value": 1.0},\n  {"timestamp": "2026-03-01T00:05:00Z", "metric": "inverter_1", "value": 2.0},\n  {"timestamp": "2026-03-01T00:10:00Z", "metric": "inverter_1", "value": 3.0},\n  {"timestamp": "2026-03-01T00:00:00Z", "metric": "inverter_2", "value": 10.0},\n  {"timestamp": "2026-03-01T00:05:00Z", "metric": "inverter_2", "value": 20.0},\n  {"timestamp": "2026-03-01T00:10:00Z", "metric": "inverter_2", "value": 30.0}\n]'
            },
        },
        {"workflow_input_name": "target_frequency", "filters": {"value": "10min"}},
    ]
}

RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "multitsframe",
            "filters": {
                "value": '[\n  {"timestamp": "2026-03-01T00:00:00Z", "metric": "inverter_1", "value": 1.0},\n  {"timestamp": "2026-03-01T00:05:00Z", "metric": "inverter_1", "value": 2.0},\n  {"timestamp": "2026-03-01T00:10:00Z", "metric": "inverter_1", "value": 3.0},\n  {"timestamp": "2026-03-01T00:00:00Z", "metric": "inverter_2", "value": 10.0},\n  {"timestamp": "2026-03-01T00:05:00Z", "metric": "inverter_2", "value": 20.0},\n  {"timestamp": "2026-03-01T00:10:00Z", "metric": "inverter_2", "value": 30.0}\n]'
            },
        },
        {"workflow_input_name": "target_frequency", "filters": {"value": "10min"}},
    ]
}
