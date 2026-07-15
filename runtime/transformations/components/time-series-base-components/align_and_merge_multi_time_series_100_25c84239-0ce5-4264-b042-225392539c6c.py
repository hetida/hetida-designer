"""Documentation for Align and Merge Multi Time Series

# Align and Merge Multi Time Series

## Description
Component to align and merge several time series from one MultiTSFrame into one
result series.

Use this component when multiple related signals belong together and should be
combined into one time series, for example several inverter power signals that
should be summed to one total power signal.

This component is the variant for an arbitrary number of time series. It reuses
`Align and Merge Two Time Series` internally for pairwise alignment and merging.
If you only want to combine exactly two separate Pandas Series inputs directly,
use `Align and Merge Two Time Series`.

This component does not resample the input. If the metric series have irregular
or different timestamps and should first be brought onto a common grid, use
`Resample Multi Time Series` before this component.

## Inputs
- **multitsframe** (Pandas DataFrame / MultiTSFrame):
    The input time series collection in long MultiTSFrame format. It must
    contain the columns `timestamp`, `metric`, and `value`.
    - `timestamp` contains the timestamps.
    - `metric` identifies the individual time series, for example
      `inverter_1` and `inverter_2`.
    - `value` contains the numeric values.
- **align_strategy** (String, default value: "exact"):
    Controls how two series are aligned in each internal pairwise merge.
    - `exact`: only identical timestamps are matched.
    - `nearest`: the temporally nearest value is matched.
    - `forward_fill`: the latest earlier value is matched.
- **join_type** (String, default value: "inner"):
    Controls which time index is used in each internal pairwise merge.
    - `inner`: keep only timestamps where both currently merged series can be
      aligned.
    - `left`: keep the index of the current combined series.
    - `right`: keep the index of the next metric series.
- **tolerance** (String, default value: null):
    Optional maximum allowed time distance for `nearest` or `forward_fill`.
    If the aligned value is farther away than this tolerance, no match is
    created. Use a fixed timedelta string such as `30s`, `5min`, or `1h`, or
    `null` to disable this check. For `align_strategy="exact"`, this input has
    no effect.
- **missing_policy** (String, default value: "keep_nan"):
    Controls what happens after each internal pairwise alignment if one side is
    missing.
    - `keep_nan`: keep the timestamp and let the merge result become `NaN` for
      operations that need both sides.
    - `drop_if_any_missing`: drop timestamps where either aligned side is
      missing before applying the merge operation.
- **merge_operation** (String, default value: "sum"):
    Defines how the aligned values from all metrics are merged into one result.
    Must be one of `sum`, `mean`, `min`, or `max`.

## Outputs
- **combined_series** (Pandas Series):
    The combined result series after alignment and merge.

## Details
1. The input must be a MultiTSFrame with the columns `timestamp`, `metric`, and
   `value`.
2. Duplicate rows with the same `timestamp` and `metric` are merged by mean.
3. The component splits the MultiTSFrame into one Pandas Series per metric.
4. The metric series are sorted by metric name to make the result reproducible.
5. The first two metric series are merged with `Align and Merge Two Time Series`.
   The result is then merged with the next metric series, and so on.
6. This means `align_strategy`, `join_type`, `tolerance`, and `missing_policy`
   behave like in version 1.0.0, but are applied repeatedly.
7. `sum`, `min`, and `max` are supported directly by repeated pairwise
   merging.
8. `mean` is also supported. It is calculated as accumulated sum divided by
   accumulated count, so each metric contributes with equal weight.
9. For `missing_policy="keep_nan"`, the mean is calculated from the aligned
   values that are available at a timestamp. For `missing_policy="drop_if_any_missing"`,
   timestamps with a missing aligned value are removed before the mean is updated.
10. Operations such as `difference`, `ratio`, `left`, or `right` are also not
    available because they are not clearly defined for an arbitrary number of
    time series.
11. If the input series are strongly irregular, either use `tolerance`
    carefully or first create a common grid with `Resample Multi Time Series`.

## Recommended Workflow
Use this component directly if all metrics already have matching timestamps, or
if you explicitly want to align the raw timestamps with `nearest` or
`forward_fill`.

For irregular timestamps, keep the two responsibilities separate:
1. Use `Resample Multi Time Series` first. Choose the desired time grid with
   `target_frequency`, for example `5min` or `1h`. Choose the aggregation
   method based on the physical meaning of the values. For power values, `mean`
   is often a reasonable default; for energy increments inside intervals, `sum`
   may be more appropriate.
2. Use `Align and Merge Multi Time Series` afterwards. If the previous step
   created a common grid, use `align_strategy="exact"` and `join_type="inner"`
   to combine the already aligned metrics.

This is usually easier to understand than doing both steps inside one
component: resampling decides the time grid, while this component decides how
the values from several metrics are combined.

## Example
```json
{
  "multitsframe": [
    {"timestamp": "2026-03-01T10:00:00Z", "metric": "inverter_1", "value": 100.0},
    {"timestamp": "2026-03-01T10:05:00Z", "metric": "inverter_1", "value": 105.0},
    {"timestamp": "2026-03-01T10:10:00Z", "metric": "inverter_1", "value": 110.0},
    {"timestamp": "2026-03-01T10:00:00Z", "metric": "inverter_2", "value": 20.0},
    {"timestamp": "2026-03-01T10:05:00Z", "metric": "inverter_2", "value": 22.0},
    {"timestamp": "2026-03-01T10:10:00Z", "metric": "inverter_2", "value": 24.0},
    {"timestamp": "2026-03-01T10:00:00Z", "metric": "inverter_3", "value": 5.0},
    {"timestamp": "2026-03-01T10:05:00Z", "metric": "inverter_3", "value": 6.0},
    {"timestamp": "2026-03-01T10:10:00Z", "metric": "inverter_3", "value": 7.0}
  ],
  "align_strategy": "exact",
  "join_type": "inner",
  "tolerance": null,
  "missing_policy": "keep_nan",
  "merge_operation": "sum"
}
```

Expected output:
```json
{
  "combined_series": {
    "2026-03-01T10:00:00Z": 125.0,
    "2026-03-01T10:05:00Z": 133.0,
    "2026-03-01T10:10:00Z": 141.0
  }
}
```

Second example with `merge_operation="mean"`:
```json
{
  "multitsframe": [
    {"timestamp": "2026-03-01T10:00:00Z", "metric": "inverter_1", "value": 100.0},
    {"timestamp": "2026-03-01T10:05:00Z", "metric": "inverter_1", "value": 105.0},
    {"timestamp": "2026-03-01T10:00:00Z", "metric": "inverter_2", "value": 20.0},
    {"timestamp": "2026-03-01T10:05:00Z", "metric": "inverter_2", "value": 25.0},
    {"timestamp": "2026-03-01T10:00:00Z", "metric": "inverter_3", "value": 10.0},
    {"timestamp": "2026-03-01T10:05:00Z", "metric": "inverter_3", "value": 20.0}
  ],
  "align_strategy": "exact",
  "join_type": "inner",
  "tolerance": null,
  "missing_policy": "keep_nan",
  "merge_operation": "mean"
}
```

Expected output:
```json
{
  "combined_series": {
    "2026-03-01T10:00:00Z": 43.3333333333,
    "2026-03-01T10:05:00Z": 50.0
  }
}
```
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from hdutils import ComponentInputValidationException
from hetdesrun.component.load import import_comp


def get_align_and_merge_two_time_series():
    return import_comp("79ffe3ff-346f-4dad-ab38-ecb7b477325d")


ALIGN_STRATEGIES = {"exact", "nearest", "forward_fill"}
JOIN_TYPES = {"inner", "left", "right"}
MISSING_POLICIES = {"keep_nan", "drop_if_any_missing"}
MERGE_OPERATIONS = {"sum", "mean", "min", "max"}
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
    if multitsframe["metric"].nunique() < 2:
        raise ComponentInputValidationException(
            "multitsframe must contain at least two different metrics",
            error_code="422",
            invalid_component_inputs=["multitsframe"],
        )


def validate_inputs(
    multitsframe: pd.DataFrame,
    align_strategy: str,
    join_type: str,
    tolerance: str | None,
    missing_policy: str,
    merge_operation: str,
) -> None:
    validate_multitsframe(multitsframe)

    if align_strategy not in ALIGN_STRATEGIES:
        raise ComponentInputValidationException(
            f"align_strategy must be one of {sorted(ALIGN_STRATEGIES)}",
            error_code="422",
            invalid_component_inputs=["align_strategy"],
        )
    if join_type not in JOIN_TYPES:
        raise ComponentInputValidationException(
            f"join_type must be one of {sorted(JOIN_TYPES)}",
            error_code="422",
            invalid_component_inputs=["join_type"],
        )
    if missing_policy not in MISSING_POLICIES:
        raise ComponentInputValidationException(
            f"missing_policy must be one of {sorted(MISSING_POLICIES)}",
            error_code="422",
            invalid_component_inputs=["missing_policy"],
        )
    if merge_operation not in MERGE_OPERATIONS:
        raise ComponentInputValidationException(
            f"merge_operation must be one of {sorted(MERGE_OPERATIONS)}",
            error_code="422",
            invalid_component_inputs=["merge_operation"],
        )

    # Let version 1.0.0 validate the exact tolerance syntax, so behavior stays identical.
    align_and_merge_two_time_series = get_align_and_merge_two_time_series()
    align_and_merge_two_time_series.validate_inputs(
        pd.Series([1.0], index=pd.DatetimeIndex([pd.Timestamp("2026-01-01T00:00:00Z")])),
        pd.Series([1.0], index=pd.DatetimeIndex([pd.Timestamp("2026-01-01T00:00:00Z")])),
        align_strategy,
        join_type,
        tolerance,
        missing_policy,
        merge_operation,
    )


def prepare_multitsframe(multitsframe: pd.DataFrame) -> pd.DataFrame:
    prepared = multitsframe[["timestamp", "metric", "value"]].copy()
    prepared["metric"] = prepared["metric"].astype(str)
    prepared["value"] = prepared["value"].astype(float)
    prepared = prepared.sort_values(["timestamp", "metric"])
    return prepared.groupby(["timestamp", "metric"], as_index=False)["value"].mean()


def build_metric_series(prepared: pd.DataFrame) -> dict[str, pd.Series]:
    metric_series = {}
    for metric, metric_frame in prepared.groupby("metric", sort=True):
        series = pd.Series(
            metric_frame["value"].to_numpy(dtype=float),
            index=pd.DatetimeIndex(metric_frame["timestamp"]),
            name=str(metric),
            dtype=float,
        ).sort_index()
        metric_series[str(metric)] = series
    return metric_series


def merge_metric_series(
    metric_series: dict[str, pd.Series],
    align_strategy: str,
    join_type: str,
    tolerance: str | None,
    missing_policy: str,
    merge_operation: str,
) -> pd.Series:
    align_and_merge_two_time_series = get_align_and_merge_two_time_series()
    ordered_series = [metric_series[metric] for metric in sorted(metric_series)]

    if merge_operation == "mean":
        return merge_metric_series_mean(
            ordered_series,
            align_strategy,
            join_type,
            tolerance,
            missing_policy,
        )

    combined = ordered_series[0]

    for next_series in ordered_series[1:]:
        combined = align_and_merge_two_time_series.main(
            timeseries_1=combined,
            timeseries_2=next_series,
            align_strategy=align_strategy,
            join_type=join_type,
            tolerance=tolerance,
            missing_policy=missing_policy,
            merge_operation=merge_operation,
        )["combined_series"]

    return combined.astype(float)


def merge_metric_series_mean(
    ordered_series: list[pd.Series],
    align_strategy: str,
    join_type: str,
    tolerance: str | None,
    missing_policy: str,
) -> pd.Series:
    align_and_merge_two_time_series = get_align_and_merge_two_time_series()
    parsed_tolerance = (
        align_and_merge_two_time_series.parse_fixed_timedelta_string(tolerance, "tolerance")
        if tolerance is not None
        else None
    )

    first_series = ordered_series[0].astype(float)
    if missing_policy == "drop_if_any_missing":
        running_sum = first_series.copy()
        running_count = pd.Series(
            np.where(first_series.notna(), 1.0, np.nan),
            index=first_series.index,
            dtype=float,
        )
    else:
        running_sum = first_series.fillna(0.0)
        running_count = pd.Series(
            np.where(first_series.notna(), 1.0, 0.0),
            index=first_series.index,
            dtype=float,
        )

    for series_to_add in ordered_series[1:]:
        next_series = series_to_add.astype(float)

        if missing_policy == "drop_if_any_missing":
            aligned_values = align_and_merge_two_time_series.build_aligned_frame(
                running_sum,
                next_series,
                align_strategy,
                join_type,
                parsed_tolerance,
            )
            aligned_values = align_and_merge_two_time_series.apply_missing_policy(
                aligned_values, missing_policy
            )
            running_sum = (aligned_values["value_1"] + aligned_values["value_2"]).astype(float)
            running_count = (running_count.reindex(running_sum.index).fillna(0.0) + 1.0).astype(
                float
            )
            continue

        aligned_sum = align_and_merge_two_time_series.build_aligned_frame(
            running_sum,
            next_series.fillna(0.0),
            align_strategy,
            join_type,
            parsed_tolerance,
        )
        running_sum = aligned_sum.fillna(0.0).sum(axis=1).astype(float)

        next_count = pd.Series(
            np.where(next_series.notna(), 1.0, 0.0),
            index=next_series.index,
            dtype=float,
        )
        aligned_count = align_and_merge_two_time_series.build_aligned_frame(
            running_count,
            next_count,
            align_strategy,
            join_type,
            parsed_tolerance,
        )
        running_count = aligned_count.fillna(0.0).sum(axis=1).astype(float)

    combined = running_sum / running_count
    combined = combined.where(running_count > 0)
    return combined.astype(float)


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "multitsframe": {"data_type": "MULTITSFRAME"},
        "align_strategy": {"data_type": "STRING", "default_value": "exact"},
        "join_type": {"data_type": "STRING", "default_value": "inner"},
        "tolerance": {"data_type": "STRING", "default_value": None},
        "missing_policy": {"data_type": "STRING", "default_value": "keep_nan"},
        "merge_operation": {"data_type": "STRING", "default_value": "sum"},
    },
    "outputs": {
        "combined_series": {"data_type": "SERIES"},
    },
    "name": "Align and Merge Multi Time Series",
    "category": "Time Series Base Components",
    "description": "Align several time series from one MultiTSFrame and merge them into one result series.",  # noqa: E501
    "version_tag": "1.0.0",
    "id": "25c84239-0ce5-4264-b042-225392539c6c",
    "revision_group_id": "fa44fdf3-cd42-48ba-bd20-fab94288bd65",
    "state": "RELEASED",
    "released_timestamp": "2026-05-11T06:00:00+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(
    *,
    multitsframe,
    align_strategy="exact",
    join_type="inner",
    tolerance=None,
    missing_policy="keep_nan",
    merge_operation="sum",
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # Step 1: Validate inputs.
    validate_inputs(
        multitsframe,
        align_strategy,
        join_type,
        tolerance,
        missing_policy,
        merge_operation,
    )

    # Step 2: Keep the MultiTSFrame columns needed for alignment and merge duplicates by mean.
    prepared = prepare_multitsframe(multitsframe)

    # Step 3: Split the MultiTSFrame into one Series per metric.
    metric_series = build_metric_series(prepared)

    # Step 4: Merge all metric series pairwise using Align and Merge Two Time Series.
    combined = merge_metric_series(
        metric_series,
        align_strategy,
        join_type,
        tolerance,
        missing_policy,
        merge_operation,
    )

    # Step 5: Return the combined result series.
    return {
        "combined_series": combined,
    }


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "multitsframe",
            "filters": {
                "value": '[\n  {"timestamp": "2026-03-01T10:00:00Z", "metric": "inverter_1", "value": 100.0},\n  {"timestamp": "2026-03-01T10:05:00Z", "metric": "inverter_1", "value": 105.0},\n  {"timestamp": "2026-03-01T10:10:00Z", "metric": "inverter_1", "value": 110.0},\n  {"timestamp": "2026-03-01T10:00:00Z", "metric": "inverter_2", "value": 20.0},\n  {"timestamp": "2026-03-01T10:05:00Z", "metric": "inverter_2", "value": 22.0},\n  {"timestamp": "2026-03-01T10:10:00Z", "metric": "inverter_2", "value": 24.0},\n  {"timestamp": "2026-03-01T10:00:00Z", "metric": "inverter_3", "value": 5.0},\n  {"timestamp": "2026-03-01T10:05:00Z", "metric": "inverter_3", "value": 6.0},\n  {"timestamp": "2026-03-01T10:10:00Z", "metric": "inverter_3", "value": 7.0}\n]'
            },
        }
    ]
}

RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "multitsframe",
            "filters": {
                "value": '[\n  {"timestamp": "2026-03-01T10:00:00Z", "metric": "inverter_1", "value": 100.0},\n  {"timestamp": "2026-03-01T10:05:00Z", "metric": "inverter_1", "value": 105.0},\n  {"timestamp": "2026-03-01T10:10:00Z", "metric": "inverter_1", "value": 110.0},\n  {"timestamp": "2026-03-01T10:00:00Z", "metric": "inverter_2", "value": 20.0},\n  {"timestamp": "2026-03-01T10:05:00Z", "metric": "inverter_2", "value": 22.0},\n  {"timestamp": "2026-03-01T10:10:00Z", "metric": "inverter_2", "value": 24.0},\n  {"timestamp": "2026-03-01T10:00:00Z", "metric": "inverter_3", "value": 5.0},\n  {"timestamp": "2026-03-01T10:05:00Z", "metric": "inverter_3", "value": 6.0},\n  {"timestamp": "2026-03-01T10:10:00Z", "metric": "inverter_3", "value": 7.0}\n]'
            },
        }
    ]
}
