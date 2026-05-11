"""Documentation for Align and Merge Two Time Series

# Align and Merge Two Time Series

## Description
Component to align two separate time series on a datetime axis and combine them
into one result series. It supports exact matching, nearest-neighbor matching, and
forward-fill matching.

## Inputs
- **timeseries_1** (Pandas Series):
    The first input time series. The index must contain timestamps, and the
    values must be numeric.
- **timeseries_2** (Pandas Series):
    The second input time series. The index must contain timestamps, and the
    values must be numeric.
- **align_strategy** (String, default value: "exact"):
    Controls how the non-reference series is aligned to the reference index.
    For `join_type="left"`, this usually means aligning `timeseries_2` to the
    index of `timeseries_1`. For `join_type="right"`, it means aligning
    `timeseries_1` to the index of `timeseries_2`.
    - `exact`: only identical timestamps are matched.
    - `nearest`: the temporally nearest value is matched.
    - `forward_fill`: the latest earlier value is matched.
- **join_type** (String, default value: "inner"):
    Controls which time index is used for the result.
    - `left`: use the index of `timeseries_1`.
    - `right`: use the index of `timeseries_2`.
    - `inner`: for `align_strategy="exact"`, use the exact timestamp
      intersection of both series. For non-exact strategies, use the index of
      `timeseries_1` as the reference index and keep only timestamps where the
      other series could be aligned successfully.
- **tolerance** (String, default value: null):
    Optional maximum allowed time distance for `nearest` or `forward_fill`.
    If the aligned value is farther away than this tolerance, no match is
    created. Use a fixed timedelta string such as `30s`, `5min`, or `1h`, or
    `null` to disable this check. For `align_strategy="exact"`, this input has
    no effect.
- **missing_policy** (String, default value: "keep_nan"):
    Controls what happens after alignment if one side is missing.
    - `keep_nan`: keep the timestamp and let the merge result become `NaN` for
      operations that need both sides.
    - `drop_if_any_missing`: drop timestamps where either aligned side is
      missing before applying the merge operation.
- **merge_operation** (String, default value: "sum"):
    Defines how the two aligned values are merged into one result.
    - `left`: use the aligned value from `timeseries_1`.
    - `right`: use the aligned value from `timeseries_2`.
    - `sum`: add both aligned values.
    - `mean`: average both aligned values.
    - `min`: take the minimum of both aligned values.
    - `max`: take the maximum of both aligned values.
    - `difference`: calculate `timeseries_1 - timeseries_2`.

## Outputs
- **combined_series** (Pandas Series):
    The combined result series after alignment and merge.

## Details
1. Both input series are sorted by time and duplicate timestamps are merged by mean.
2. Depending on `join_type`, either `timeseries_1`, `timeseries_2`, or an
   exact timestamp intersection is used as the reference index.
3. Depending on `align_strategy`, the non-reference series is aligned by exact
   matching, nearest-neighbor matching, or forward-fill matching.
   For `join_type="right"`, this means that `timeseries_1` is aligned to the
   index of `timeseries_2`.
4. If `tolerance` is set, matches that are farther away than this threshold are
   rejected for `nearest` and `forward_fill`.
   For `align_strategy="exact"`, `tolerance` is ignored.
5. After alignment, `missing_policy` decides whether timestamps with missing
   aligned values are kept or dropped.
6. Finally, `merge_operation` combines the two aligned values into one result
   value per timestamp.
7. If both series are strongly irregular or visibly offset in time, it is often
   better to first bring them onto a shared grid with `resample_time_series`
   and only then use this component.
8. The `inner` mode is symmetric only for `align_strategy="exact"`. For
   non-exact strategies, `inner` uses `timeseries_1` as the reference index
   and then keeps only timestamps with successful matches from the other side.

## Example
```json
{
  "timeseries_1": {
    "2026-03-01T10:00:00Z": 100.0,
    "2026-03-01T10:05:00Z": 105.0,
    "2026-03-01T10:10:00Z": 110.0
  },
  "timeseries_2": {
    "2026-03-01T10:00:00Z": 20.0,
    "2026-03-01T10:05:00Z": 22.0,
    "2026-03-01T10:10:00Z": 24.0
  },
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
    "2026-03-01T10:00:00Z": 120.0,
    "2026-03-01T10:05:00Z": 127.0,
    "2026-03-01T10:10:00Z": 134.0
  }
}
```

Second example with `nearest`:
```json
{
  "timeseries_1": {
    "2026-03-01T10:00:00Z": 100.0,
    "2026-03-01T10:05:00Z": 105.0,
    "2026-03-01T10:10:00Z": 110.0
  },
  "timeseries_2": {
    "2026-03-01T10:00:20Z": 20.0,
    "2026-03-01T10:05:15Z": 22.0,
    "2026-03-01T10:11:00Z": 24.0
  },
  "align_strategy": "nearest",
  "join_type": "left",
  "tolerance": "30s",
  "missing_policy": "drop_if_any_missing",
  "merge_operation": "sum"
}
```

Expected output:
```json
{
  "combined_series": {
    "2026-03-01T10:00:00Z": 120.0,
    "2026-03-01T10:05:00Z": 127.0
  }
}
```
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from hdutils import ComponentInputValidationException, parse_default_value

ALIGN_STRATEGIES = {"exact", "nearest", "forward_fill"}
JOIN_TYPES = {"inner", "left", "right"}
MISSING_POLICIES = {"keep_nan", "drop_if_any_missing"}
MERGE_OPERATIONS = {"left", "right", "sum", "mean", "min", "max", "difference"}


def parse_fixed_timedelta_string(value: str, input_name: str) -> pd.Timedelta:
    try:
        offset = pd.tseries.frequencies.to_offset(value)
    except ValueError as exc:
        raise ComponentInputValidationException(
            f"{input_name} must be a valid fixed timedelta string like '30s', '5min', or '1h'",
            error_code="422",
            invalid_component_inputs=[input_name],
        ) from exc

    try:
        nanos = offset.nanos
    except ValueError as exc:
        raise ComponentInputValidationException(
            f"{input_name} must be a fixed timedelta string like '30s', '5min', or '1h'",
            error_code="422",
            invalid_component_inputs=[input_name],
        ) from exc

    return pd.to_timedelta(nanos, unit="ns")


def validate_series(timeseries: pd.Series, input_name: str) -> None:
    if not isinstance(timeseries, pd.Series):
        raise ComponentInputValidationException(
            f"{input_name} must be a pandas Series",
            error_code="422",
            invalid_component_inputs=[input_name],
        )
    if timeseries.empty:
        raise ComponentInputValidationException(
            f"{input_name} must not be empty",
            error_code="422",
            invalid_component_inputs=[input_name],
        )
    if not pd.api.types.is_datetime64_any_dtype(timeseries.index):
        raise ComponentInputValidationException(
            f"{input_name} index must be datetime",
            error_code="422",
            invalid_component_inputs=[input_name],
        )
    if not pd.api.types.is_numeric_dtype(timeseries):
        raise ComponentInputValidationException(
            f"{input_name} values must be numeric",
            error_code="422",
            invalid_component_inputs=[input_name],
        )
    if not np.isfinite(timeseries.dropna().to_numpy(dtype=float)).all():
        raise ComponentInputValidationException(
            f"{input_name} must not contain inf or -inf values",
            error_code="422",
            invalid_component_inputs=[input_name],
        )
    if timeseries.dropna().empty:
        raise ComponentInputValidationException(
            f"{input_name} must contain at least one non-missing numeric value",
            error_code="422",
            invalid_component_inputs=[input_name],
        )


def validate_inputs(
    timeseries_1: pd.Series,
    timeseries_2: pd.Series,
    align_strategy: str,
    join_type: str,
    tolerance: str | None,
    missing_policy: str,
    merge_operation: str,
) -> pd.Timedelta | None:
    validate_series(timeseries_1, "timeseries_1")
    validate_series(timeseries_2, "timeseries_2")

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

    parsed_tolerance = None
    if tolerance is not None:
        parsed_tolerance = parse_fixed_timedelta_string(tolerance, "tolerance")
        if parsed_tolerance <= pd.Timedelta(0):
            raise ComponentInputValidationException(
                "tolerance must be greater than zero",
                error_code="422",
                invalid_component_inputs=["tolerance"],
            )

    return parsed_tolerance


def prepare_series(timeseries: pd.Series) -> pd.Series:
    prepared = timeseries.sort_index()
    if not prepared.index.is_unique:
        prepared = prepared.groupby(level=0).mean()
    return prepared.astype(float)


def align_series_to_reference(
    reference_index: pd.DatetimeIndex,
    source_series: pd.Series,
    align_strategy: str,
    tolerance: pd.Timedelta | None,
) -> pd.Series:
    if align_strategy == "exact":
        return source_series.reindex(reference_index)

    reference_frame = pd.DataFrame({"timestamp": reference_index})
    source_frame = source_series.rename("value").reset_index()
    source_frame.columns = ["timestamp", "value"]

    direction = "nearest" if align_strategy == "nearest" else "backward"
    merged = pd.merge_asof(
        reference_frame,
        source_frame,
        on="timestamp",
        direction=direction,
        tolerance=tolerance,
    )
    return pd.Series(merged["value"].to_numpy(dtype=float), index=reference_index, dtype=float)


def build_aligned_frame(
    series_1: pd.Series,
    series_2: pd.Series,
    align_strategy: str,
    join_type: str,
    tolerance: pd.Timedelta | None,
) -> pd.DataFrame:
    if join_type == "right":
        reference_index = series_2.index
        aligned_1 = align_series_to_reference(reference_index, series_1, align_strategy, tolerance)
        aligned_2 = series_2.reindex(reference_index)
    elif join_type == "left":
        reference_index = series_1.index
        aligned_1 = series_1.reindex(reference_index)
        aligned_2 = align_series_to_reference(reference_index, series_2, align_strategy, tolerance)
    elif align_strategy == "exact":
        reference_index = series_1.index.intersection(series_2.index)
        aligned_1 = series_1.reindex(reference_index)
        aligned_2 = series_2.reindex(reference_index)
    else:
        reference_index = series_1.index
        aligned_1 = series_1.reindex(reference_index)
        aligned_2 = align_series_to_reference(reference_index, series_2, align_strategy, tolerance)
        matched = aligned_1.notna() & aligned_2.notna()
        aligned_1 = aligned_1[matched]
        aligned_2 = aligned_2[matched]

    return pd.DataFrame({"value_1": aligned_1, "value_2": aligned_2})


def apply_missing_policy(aligned: pd.DataFrame, missing_policy: str) -> pd.DataFrame:
    if missing_policy == "drop_if_any_missing":
        return aligned.dropna(how="any")
    return aligned


def merge_aligned_values(aligned: pd.DataFrame, merge_operation: str) -> pd.Series:
    value_1 = aligned["value_1"]
    value_2 = aligned["value_2"]

    if merge_operation == "left":
        result = value_1
    elif merge_operation == "right":
        result = value_2
    elif merge_operation == "sum":
        result = value_1 + value_2
    elif merge_operation == "mean":
        result = (value_1 + value_2) / 2.0
    elif merge_operation == "min":
        result = aligned[["value_1", "value_2"]].min(axis=1, skipna=False)
    elif merge_operation == "max":
        result = aligned[["value_1", "value_2"]].max(axis=1, skipna=False)
    else:
        result = value_1 - value_2

    return result.astype(float)


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "timeseries_1": {"data_type": "SERIES"},
        "timeseries_2": {"data_type": "SERIES"},
        "align_strategy": {"data_type": "STRING", "default_value": "exact"},
        "join_type": {"data_type": "STRING", "default_value": "inner"},
        "tolerance": {"data_type": "STRING", "default_value": None},
        "missing_policy": {"data_type": "STRING", "default_value": "keep_nan"},
        "merge_operation": {"data_type": "STRING", "default_value": "sum"},
    },
    "outputs": {
        "combined_series": {"data_type": "SERIES"},
    },
    "name": "Align and Merge Two Time Series",
    "category": "Time Series Base Components",
    "description": "Align two separate time series on time and merge them into one result series.",
    "version_tag": "1.0.0",
    "id": "79ffe3ff-346f-4dad-ab38-ecb7b477325d",
    "revision_group_id": "212ead20-b2e7-4ca7-9eb5-c38c6f32e23b",
    "state": "RELEASED",
    "released_timestamp": "2026-05-11T08:00:00+02:00",
}


def main(
    *,
    timeseries_1,
    timeseries_2,
    align_strategy=parse_default_value(COMPONENT_INFO, "align_strategy"),
    join_type=parse_default_value(COMPONENT_INFO, "join_type"),
    tolerance=parse_default_value(COMPONENT_INFO, "tolerance"),
    missing_policy=parse_default_value(COMPONENT_INFO, "missing_policy"),
    merge_operation=parse_default_value(COMPONENT_INFO, "merge_operation"),
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # Step 1: Validate inputs and parse the optional tolerance.
    parsed_tolerance = validate_inputs(
        timeseries_1,
        timeseries_2,
        align_strategy,
        join_type,
        tolerance,
        missing_policy,
        merge_operation,
    )

    # Step 2: Sort both series and merge duplicate timestamps by mean.
    prepared_1 = prepare_series(timeseries_1)
    prepared_2 = prepare_series(timeseries_2)

    # Step 3: Align both series on the selected reference index.
    aligned = build_aligned_frame(
        prepared_1,
        prepared_2,
        align_strategy,
        join_type,
        parsed_tolerance,
    )

    # Step 4: Apply the selected missing-value policy.
    aligned = apply_missing_policy(aligned, missing_policy)

    # Step 5: Merge the aligned values into one result series.
    combined = merge_aligned_values(aligned, merge_operation)

    # Step 6: Return the combined result series.
    return {
        "combined_series": combined,
    }


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "timeseries_1",
            "filters": {
                "value": '{\n    "2026-03-01T10:00:00Z": 100.0,\n    "2026-03-01T10:05:00Z": 105.0,\n    "2026-03-01T10:10:00Z": 110.0\n}'
            },
        },
        {
            "workflow_input_name": "timeseries_2",
            "filters": {
                "value": '{\n    "2026-03-01T10:00:00Z": 20.0,\n    "2026-03-01T10:05:00Z": 22.0,\n    "2026-03-01T10:10:00Z": 24.0\n}'
            },
        },
    ]
}

RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "timeseries_1",
            "filters": {
                "value": '{\n    "2026-03-01T10:00:00Z": 100.0,\n    "2026-03-01T10:05:00Z": 105.0,\n    "2026-03-01T10:10:00Z": 110.0\n}'
            },
        },
        {
            "workflow_input_name": "timeseries_2",
            "filters": {
                "value": '{\n    "2026-03-01T10:00:00Z": 20.0,\n    "2026-03-01T10:05:00Z": 22.0,\n    "2026-03-01T10:10:00Z": 24.0\n}'
            },
        },
    ]
}
