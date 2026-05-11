"""Documentation for Handle Gaps and Missing Data

# Handle Gaps and Missing Data

## Description
Single-point component to detect gaps (missing values and missing timestamps),
optionally fill them, and return a corrected series.

## Inputs
- **timeseries** (Pandas Series):
    The input time series. Index must be datetime, values numeric.
    Optional metadata in `timeseries.attrs` is supported:
    `ref_interval_start_timestamp` / `from` and
    `ref_interval_end_timestamp` / `to`.
- **mode** (String, default value: "fill"):
    One of "fill", "flag", "drop".
- **method** (String, default value: "time"):
    Filling method. One of "time", "linear", "ffill", "bfill", "constant".
- **limit_direction** (String, default value: "both"):
    Interpolation direction for "time"/"linear" ("forward", "backward", "both").
- **min_gap_length** (Integer, default value: 1):
    Minimum number of consecutive missing points to consider a gap fillable.
- **max_gap_length** (Integer, default value: 6):
    Maximum length of fillable gaps. Standard is deliberately conservative.
    Larger gaps are left as missing values.
- **constant_value** (Float, default value: 0):
    Constant value used when method="constant".
- **resample_to** (String, default value: null):
    Optional target frequency (e.g. "10min") to create a regular grid.
    Missing timestamps on the grid are treated as gaps.
- **auto_frequency_determination** (Boolean, default value: True):
    If True and resample_to is not set, infer a regular frequency from the
    median time difference and resample to that grid.

## Outputs
- **corrected_timeseries** (Pandas Series):
    The resulting series (filled/flagged/dropped depending on mode).

## Details
1. Sorts the input by time and removes duplicate timestamps (keeps the mean).
2. Optionally resamples to a regular grid to make missing timestamps visible.
3. Detects gaps as NaN values and as missing timestamps on the grid.
4. If resample_to is set, it takes precedence over auto-frequency detection.
5. Optionally infers a regular grid from the median time difference.
6. Optionally extends/restricts the grid to the reference interval from
   metadata (`ref_interval_start_timestamp`/`from`,
   `ref_interval_end_timestamp`/`to`).
   If metadata provides `ref_data_frequency` (and optionally
   `ref_data_frequency_offset`), these values are preferred for grid building.
   If interval boundaries are not aligned to the detected grid, boundaries are
   snapped to the nearest inner grid points while preserving the original
   timestamp phase of the series.
7. Fills only gaps within the configured length limits.
8. Returns the processed series.

## Example
```json
{
  "timeseries": {
    "2026-01-12T00:00:00Z": 10,
    "2026-01-12T00:07:00Z": 12,
    "2026-01-12T00:13:00Z": 13,
    "2026-01-12T00:18:00Z": 14,
    "2026-01-12T00:22:00Z": 15,
    "2026-01-12T00:25:00Z": 15,
    "2026-01-12T00:32:00Z": 15,
    "2026-01-12T00:38:00Z": 14,
    "2026-01-12T00:43:00Z": 13,
    "2026-01-12T00:47:00Z": 12,
    "2026-01-12T00:50:00Z": 11,
    "2026-01-12T00:57:00Z": 10,
    "2026-01-12T01:03:00Z": null,
    "2026-01-12T01:08:00Z": 9,
    "2026-01-12T01:12:00Z": 9,
    "2026-01-12T01:15:00Z": 10,
    "2026-01-12T01:22:00Z": 11,
    "2026-01-12T01:28:00Z": 12,
    "2026-01-12T01:33:00Z": 14,
    "2026-01-12T01:37:00Z": 15,
    "2026-01-12T01:40:00Z": 17,
    "2026-01-12T01:47:00Z": 18,
    "2026-01-12T01:53:00Z": 18,
    "2026-01-12T01:58:00Z": 19,
    "2026-01-12T02:02:00Z": 18,
    "2026-01-12T02:05:00Z": 18,
    "2026-01-12T02:12:00Z": 16,
    "2026-01-12T02:18:00Z": 15,
    "2026-01-12T02:23:00Z": 14,
    "2026-01-12T02:27:00Z": 13,
    "2026-01-12T02:30:00Z": null,
    "2026-01-12T02:37:00Z": null,
    "2026-01-12T02:43:00Z": null,
    "2026-01-12T02:48:00Z": 13,
    "2026-01-12T02:52:00Z": 14,
    "2026-01-12T02:55:00Z": 15,
    "2026-01-12T03:02:00Z": 16,
    "2026-01-12T03:08:00Z": 18,
    "2026-01-12T03:13:00Z": 19,
    "2026-01-12T03:17:00Z": 20,
    "2026-01-12T03:20:00Z": 21,
    "2026-01-12T03:27:00Z": 21,
    "2026-01-12T03:33:00Z": 20,
    "2026-01-12T03:38:00Z": 20,
    "2026-01-12T03:42:00Z": 19,
    "2026-01-12T03:45:00Z": 17,
    "2026-01-12T03:52:00Z": 16,
    "2026-01-12T03:58:00Z": 15,
    "2026-01-12T04:03:00Z": 14,
    "2026-01-12T04:07:00Z": 13,
    "2026-01-12T04:10:00Z": 13,
    "2026-01-12T04:17:00Z": 14,
    "2026-01-12T04:23:00Z": 15,
    "2026-01-12T04:28:00Z": 16,
    "2026-01-12T04:32:00Z": null,
    "2026-01-12T04:35:00Z": null,
    "2026-01-12T04:42:00Z": null,
    "2026-01-12T04:48:00Z": null,
    "2026-01-12T04:53:00Z": null,
    "2026-01-12T04:57:00Z": null,
    "2026-01-12T05:00:00Z": 21,
    "2026-01-12T05:07:00Z": 20,
    "2026-01-12T05:13:00Z": 19
},
  "max_gap_length": 4
}
```
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from hdutils import ComponentInputValidationException


def validate_inputs(
    series: pd.Series,
    mode: str,
    method: str,
    limit_direction: str,
    min_gap_length: int,
    max_gap_length: int | None,
    constant_value: float,
    resample_to: str | None,
    auto_frequency_determination: bool,
) -> None:
    if not isinstance(series, pd.Series):
        raise ComponentInputValidationException(
            "timeseries must be a pandas Series",
            error_code="422",
            invalid_component_inputs=["timeseries"],
        )
    if not pd.api.types.is_datetime64_any_dtype(series.index):
        raise ComponentInputValidationException(
            "timeseries index must be datetime",
            error_code="422",
            invalid_component_inputs=["timeseries"],
        )
    if mode not in {"fill", "flag", "drop"}:
        raise ComponentInputValidationException(
            f"mode must be one of 'fill', 'flag', 'drop', got '{mode}'",
            error_code="422",
            invalid_component_inputs=["mode"],
        )
    if method not in {"time", "linear", "ffill", "bfill", "constant"}:
        raise ComponentInputValidationException(
            f"method must be one of 'time', 'linear', 'ffill', 'bfill', 'constant', got '{method}'",
            error_code="422",
            invalid_component_inputs=["method"],
        )
    if limit_direction not in {"forward", "backward", "both"}:
        raise ComponentInputValidationException(
            "limit_direction must be one of 'forward', 'backward', 'both'",
            error_code="422",
            invalid_component_inputs=["limit_direction"],
        )
    if not isinstance(min_gap_length, int):
        raise ComponentInputValidationException(
            "min_gap_length must be an integer >= 1",
            error_code="422",
            invalid_component_inputs=["min_gap_length"],
        )
    if min_gap_length < 1:
        raise ComponentInputValidationException(
            "min_gap_length must be >= 1",
            error_code="422",
            invalid_component_inputs=["min_gap_length"],
        )
    if max_gap_length is not None and not isinstance(max_gap_length, int):
        raise ComponentInputValidationException(
            "max_gap_length must be an integer >= min_gap_length or null",
            error_code="422",
            invalid_component_inputs=["max_gap_length"],
        )
    if max_gap_length is not None and max_gap_length < min_gap_length:
        raise ComponentInputValidationException(
            "max_gap_length must be >= min_gap_length",
            error_code="422",
            invalid_component_inputs=["max_gap_length"],
        )
    if mode == "fill" and method == "constant":
        if not isinstance(constant_value, (int, float)):
            raise ComponentInputValidationException(
                "constant_value must be a number",
                error_code="422",
                invalid_component_inputs=["constant_value"],
            )
        if not np.isfinite(float(constant_value)):
            raise ComponentInputValidationException(
                "constant_value must be a finite number",
                error_code="422",
                invalid_component_inputs=["constant_value"],
            )
    if resample_to is not None and not isinstance(resample_to, str):
        raise ComponentInputValidationException(
            "resample_to must be a frequency string like '5min' or null",
            error_code="422",
            invalid_component_inputs=["resample_to"],
        )
    if not isinstance(auto_frequency_determination, bool):
        raise ComponentInputValidationException(
            "auto_frequency_determination must be true or false",
            error_code="422",
            invalid_component_inputs=["auto_frequency_determination"],
        )


def gap_lengths(mask: pd.Series) -> pd.Series:
    """Return gap length for each position in a boolean gap mask."""
    group = (mask != mask.shift()).cumsum()
    return mask.groupby(group).transform("sum")


def get_reference_interval_from_series_attrs(
    series: pd.Series,
) -> tuple[pd.Timestamp | None, pd.Timestamp | None]:
    """Read optional interval boundaries from series metadata.

    Supported keys:
    - start: ``ref_interval_start_timestamp`` or ``from``
    - end: ``ref_interval_end_timestamp`` or ``to``
    """

    attrs = series.attrs if isinstance(series.attrs, dict) else {}
    dataset_metadata = attrs.get("dataset_metadata")

    start_raw = None
    end_raw = None
    if isinstance(dataset_metadata, dict):
        start_raw = dataset_metadata.get(
            "ref_interval_start_timestamp", dataset_metadata.get("from")
        )
        end_raw = dataset_metadata.get("ref_interval_end_timestamp", dataset_metadata.get("to"))

    if start_raw is None:
        start_raw = attrs.get("ref_interval_start_timestamp", attrs.get("from"))
    if end_raw is None:
        end_raw = attrs.get("ref_interval_end_timestamp", attrs.get("to"))

    start_ts: pd.Timestamp | None = None
    end_ts: pd.Timestamp | None = None

    if start_raw is not None:
        try:
            start_ts = pd.Timestamp(start_raw)
        except (TypeError, ValueError) as exc:
            raise ComponentInputValidationException(
                "timeseries metadata field 'ref_interval_start_timestamp' (or 'from') is not a valid timestamp",
                error_code="422",
                invalid_component_inputs=["timeseries"],
            ) from exc

    if end_raw is not None:
        try:
            end_ts = pd.Timestamp(end_raw)
        except (TypeError, ValueError) as exc:
            raise ComponentInputValidationException(
                "timeseries metadata field 'ref_interval_end_timestamp' (or 'to') is not a valid timestamp",
                error_code="422",
                invalid_component_inputs=["timeseries"],
            ) from exc

    if start_ts is not None and end_ts is not None and start_ts > end_ts:
        raise ComponentInputValidationException(
            "timeseries metadata interval is invalid: start is after end",
            error_code="422",
            invalid_component_inputs=["timeseries"],
        )

    return start_ts, end_ts


def get_reference_frequency_from_series_attrs(series: pd.Series) -> str | None:
    """Read optional reference frequency from series metadata."""

    attrs = series.attrs if isinstance(series.attrs, dict) else {}
    dataset_metadata = attrs.get("dataset_metadata")

    freq_raw = None
    if isinstance(dataset_metadata, dict):
        freq_raw = dataset_metadata.get("ref_data_frequency")
    if freq_raw is None:
        freq_raw = attrs.get("ref_data_frequency")

    if freq_raw is None:
        return None
    if not isinstance(freq_raw, str):
        raise ComponentInputValidationException(
            "timeseries metadata field 'ref_data_frequency' must be a frequency string",
            error_code="422",
            invalid_component_inputs=["timeseries"],
        )

    return freq_raw


def get_reference_frequency_offset_from_series_attrs(series: pd.Series) -> str | None:
    """Read optional reference frequency offset from series metadata."""

    attrs = series.attrs if isinstance(series.attrs, dict) else {}
    dataset_metadata = attrs.get("dataset_metadata")

    offset_raw = None
    if isinstance(dataset_metadata, dict):
        offset_raw = dataset_metadata.get("ref_data_frequency_offset")
    if offset_raw is None:
        offset_raw = attrs.get("ref_data_frequency_offset")

    if offset_raw is None:
        return None
    if not isinstance(offset_raw, str):
        raise ComponentInputValidationException(
            "timeseries metadata field 'ref_data_frequency_offset' must be a duration string",
            error_code="422",
            invalid_component_inputs=["timeseries"],
        )

    return offset_raw


def build_regular_grid_from_frequency(
    ordered: pd.Series,
    frequency: str | pd.Timedelta,
) -> pd.Series:
    full_index = pd.date_range(start=ordered.index.min(), end=ordered.index.max(), freq=frequency)
    return ordered.reindex(full_index)


def resolve_frequency_for_window(
    ordered: pd.Series,
    resample_to: str | None,
    auto_frequency_determination: bool,
    reference_frequency: str | None,
) -> tuple[pd.Series, str | pd.Timedelta | None]:
    resample_value = resample_to
    if resample_value is False or resample_value == "":
        resample_value = None

    if resample_value:
        try:
            ordered = build_regular_grid_from_frequency(ordered, resample_value)
        except (ValueError, TypeError) as exc:
            raise ComponentInputValidationException(
                f"resample_to could not be parsed as frequency: {resample_value}",
                error_code="422",
                invalid_component_inputs=["resample_to"],
            ) from exc
        return ordered, resample_value

    if reference_frequency and len(ordered.index) > 1:
        try:
            ref_freq_delta = pd.to_timedelta(reference_frequency)
        except (TypeError, ValueError) as exc:
            raise ComponentInputValidationException(
                "timeseries metadata field 'ref_data_frequency' is not a valid frequency",
                error_code="422",
                invalid_component_inputs=["timeseries"],
            ) from exc
        if ref_freq_delta <= pd.Timedelta(0):
            raise ComponentInputValidationException(
                "timeseries metadata field 'ref_data_frequency' must be positive",
                error_code="422",
                invalid_component_inputs=["timeseries"],
            )
        ordered = build_regular_grid_from_frequency(ordered, ref_freq_delta)
        return ordered, ref_freq_delta

    if auto_frequency_determination and len(ordered.index) > 1:
        diffs = ordered.index.to_series().diff().dropna()
        positive_diffs = diffs[diffs > pd.Timedelta(0)]
        if positive_diffs.empty:
            raise ComponentInputValidationException(
                "Cannot infer frequency from timestamps after sorting",
                error_code="422",
                invalid_component_inputs=["auto_frequency_determination"],
            )
        inferred = positive_diffs.median()
        if inferred <= pd.Timedelta(0):
            raise ComponentInputValidationException(
                "Inferred frequency must be positive",
                error_code="422",
                invalid_component_inputs=["auto_frequency_determination"],
            )
        ordered = build_regular_grid_from_frequency(ordered, inferred)
        return ordered, inferred

    return ordered, None


def resolve_frequency_delta_for_window(
    ordered: pd.Series,
    frequency_for_window: str | pd.Timedelta | None,
) -> pd.Timedelta:
    if frequency_for_window is None:
        diffs = ordered.index.to_series().diff().dropna()
        positive_diffs = diffs[diffs > pd.Timedelta(0)]
        if positive_diffs.empty:
            raise ComponentInputValidationException(
                "Cannot apply metadata interval without a detectable positive frequency",
                error_code="422",
                invalid_component_inputs=["timeseries"],
            )
        frequency_for_window = positive_diffs.median()

    try:
        freq_delta = pd.to_timedelta(frequency_for_window)
    except (TypeError, ValueError) as exc:
        raise ComponentInputValidationException(
            "Cannot apply metadata interval because frequency is not a fixed timedelta",
            error_code="422",
            invalid_component_inputs=["timeseries"],
        ) from exc
    if freq_delta <= pd.Timedelta(0):
        raise ComponentInputValidationException(
            "Cannot apply metadata interval because frequency must be positive",
            error_code="422",
            invalid_component_inputs=["timeseries"],
        )
    return freq_delta


def apply_reference_window_to_series(
    ordered: pd.Series,
    window_start: pd.Timestamp | None,
    window_end: pd.Timestamp | None,
    reference_frequency_offset: str | None,
    frequency_for_window: str | pd.Timedelta | None,
) -> pd.Series:
    if window_start is None and window_end is None:
        return ordered
    if ordered.empty:
        raise ComponentInputValidationException(
            "Cannot apply metadata interval to an empty timeseries",
            error_code="422",
            invalid_component_inputs=["timeseries"],
        )

    freq_delta = resolve_frequency_delta_for_window(ordered, frequency_for_window)

    target_start = window_start if window_start is not None else ordered.index.min()
    target_end = window_end if window_end is not None else ordered.index.max()
    if target_start > target_end:
        raise ComponentInputValidationException(
            "Metadata interval start must be before or equal to end",
            error_code="422",
            invalid_component_inputs=["timeseries"],
        )

    # Keep the original timestamp phase (e.g. full hour) across the whole window.
    anchor = ordered.index.min()
    if reference_frequency_offset is not None:
        try:
            offset_delta = pd.to_timedelta(reference_frequency_offset)
        except (TypeError, ValueError) as exc:
            raise ComponentInputValidationException(
                "timeseries metadata field 'ref_data_frequency_offset' is not a valid duration",
                error_code="422",
                invalid_component_inputs=["timeseries"],
            ) from exc
        offset_mod = offset_delta % freq_delta
        epoch_anchor = pd.Timestamp("1970-01-01", tz=ordered.index.min().tz)
        anchor = epoch_anchor + offset_mod

    start_steps = int(np.ceil((target_start - anchor) / freq_delta))
    end_steps = int(np.floor((target_end - anchor) / freq_delta))
    aligned_start = anchor + start_steps * freq_delta
    aligned_end = anchor + end_steps * freq_delta

    if aligned_start > aligned_end:
        return ordered.iloc[0:0]

    full_window_index = pd.date_range(start=aligned_start, end=aligned_end, freq=freq_delta)
    return ordered.reindex(full_window_index)


def prepare_series(
    series: pd.Series,
    resample_to: str | None,
    auto_frequency_determination: bool,
    reference_frequency: str | None = None,
    reference_frequency_offset: str | None = None,
    window_start: pd.Timestamp | None = None,
    window_end: pd.Timestamp | None = None,
) -> pd.Series:
    ordered = series.sort_index()
    if not ordered.index.is_unique:
        ordered = ordered.groupby(level=0).mean()
    ordered, frequency_for_window = resolve_frequency_for_window(
        ordered,
        resample_to,
        auto_frequency_determination,
        reference_frequency,
    )
    return apply_reference_window_to_series(
        ordered,
        window_start=window_start,
        window_end=window_end,
        reference_frequency_offset=reference_frequency_offset,
        frequency_for_window=frequency_for_window,
    )


def fill_series(
    series: pd.Series,
    fillable_mask: pd.Series,
    method: str,
    limit_direction: str,
    constant_value: float,
) -> pd.Series:
    if method == "constant":
        filled = series.copy()
        filled.loc[fillable_mask] = constant_value
        return filled

    if method in {"ffill", "bfill"}:
        filled = series.ffill() if method == "ffill" else series.bfill()
    else:
        filled = series.interpolate(method=method, limit_direction=limit_direction)

    # Restore non-fillable missing points
    filled.loc[~fillable_mask & series.isna()] = np.nan
    return filled


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "timeseries": {"data_type": "SERIES"},
        "mode": {"data_type": "STRING", "default_value": "fill"},
        "method": {"data_type": "STRING", "default_value": "time"},
        "limit_direction": {"data_type": "STRING", "default_value": "both"},
        "auto_frequency_determination": {"data_type": "BOOLEAN", "default_value": True},
        "min_gap_length": {"data_type": "INT", "default_value": 1},
        "max_gap_length": {"data_type": "INT", "default_value": 6},
        "constant_value": {"data_type": "FLOAT", "default_value": 0.0},
        "resample_to": {"data_type": "STRING", "default_value": None},
    },
    "outputs": {
        "corrected_timeseries": {"data_type": "SERIES"},
    },
    "name": "Handle Gaps and Missing Data",
    "category": "Time Series Base Components",
    "description": "Detect and optionally fill gaps in time series.",
    "version_tag": "1.0.0",
    "id": "06b9bb8f-513f-4304-8f86-2bf6d5ba32f1",
    "revision_group_id": "2c3fb56e-5288-42a0-aa91-4417b29fb2af",
    "state": "RELEASED",
    "released_timestamp": "2026-05-11T08:00:00+02:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(
    *,
    timeseries,
    mode="fill",
    method="time",
    limit_direction="both",
    auto_frequency_determination=True,
    min_gap_length=1,
    max_gap_length=6,
    constant_value=0.0,
    resample_to=None,
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    validate_inputs(
        timeseries,
        mode,
        method,
        limit_direction,
        min_gap_length,
        max_gap_length,
        constant_value,
        resample_to,
        auto_frequency_determination,
    )
    ref_interval_start, ref_interval_end = get_reference_interval_from_series_attrs(timeseries)
    ref_data_frequency = get_reference_frequency_from_series_attrs(timeseries)
    ref_data_frequency_offset = get_reference_frequency_offset_from_series_attrs(timeseries)
    series = prepare_series(
        timeseries,
        resample_to,
        auto_frequency_determination,
        reference_frequency=ref_data_frequency,
        reference_frequency_offset=ref_data_frequency_offset,
        window_start=ref_interval_start,
        window_end=ref_interval_end,
    )

    missing_mask = series.isna()
    gap_lengths_values = gap_lengths(missing_mask)
    fillable_mask = missing_mask & (gap_lengths_values >= min_gap_length)
    if max_gap_length is not None:
        fillable_mask &= gap_lengths_values <= max_gap_length

    if mode == "fill":
        processed = fill_series(
            series,
            fillable_mask,
            method,
            limit_direction,
            constant_value,
        )
    elif mode == "drop":
        processed = series.copy()
        processed = processed.dropna()
    else:
        processed = series.copy()

    return {
        "corrected_timeseries": processed,
    }


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "timeseries",
            "filters": {
                "value": '{\n    "2026-01-12T00:00:00Z": 10,\n    "2026-01-12T00:07:00Z": 12,\n    "2026-01-12T00:13:00Z": 13,\n    "2026-01-12T00:18:00Z": 14,\n    "2026-01-12T00:22:00Z": 15,\n    "2026-01-12T00:25:00Z": 15,\n    "2026-01-12T00:32:00Z": 15,\n    "2026-01-12T00:38:00Z": 14,\n    "2026-01-12T00:43:00Z": 13,\n    "2026-01-12T00:47:00Z": 12,\n    "2026-01-12T00:50:00Z": 11,\n    "2026-01-12T00:57:00Z": 10,\n    "2026-01-12T01:03:00Z": null,\n    "2026-01-12T01:08:00Z": 9,\n    "2026-01-12T01:12:00Z": 9,\n    "2026-01-12T01:15:00Z": 10,\n    "2026-01-12T01:22:00Z": 11,\n    "2026-01-12T01:28:00Z": 12,\n    "2026-01-12T01:33:00Z": 14,\n    "2026-01-12T01:37:00Z": 15,\n    "2026-01-12T01:40:00Z": 17,\n    "2026-01-12T01:47:00Z": 18,\n    "2026-01-12T01:53:00Z": 18,\n    "2026-01-12T01:58:00Z": 19,\n    "2026-01-12T02:02:00Z": 18,\n    "2026-01-12T02:05:00Z": 18,\n    "2026-01-12T02:12:00Z": 16,\n    "2026-01-12T02:18:00Z": 15,\n    "2026-01-12T02:23:00Z": 14,\n    "2026-01-12T02:27:00Z": 13,\n    "2026-01-12T02:30:00Z": null,\n    "2026-01-12T02:37:00Z": null,\n    "2026-01-12T02:43:00Z": null,\n    "2026-01-12T02:48:00Z": 13,\n    "2026-01-12T02:52:00Z": 14,\n    "2026-01-12T02:55:00Z": 15,\n    "2026-01-12T03:02:00Z": 16,\n    "2026-01-12T03:08:00Z": 18,\n    "2026-01-12T03:13:00Z": 19,\n    "2026-01-12T03:17:00Z": 20,\n    "2026-01-12T03:20:00Z": 21,\n    "2026-01-12T03:27:00Z": 21,\n    "2026-01-12T03:33:00Z": 20,\n    "2026-01-12T03:38:00Z": 20,\n    "2026-01-12T03:42:00Z": 19,\n    "2026-01-12T03:45:00Z": 17,\n    "2026-01-12T03:52:00Z": 16,\n    "2026-01-12T03:58:00Z": 15,\n    "2026-01-12T04:03:00Z": 14,\n    "2026-01-12T04:07:00Z": 13,\n    "2026-01-12T04:10:00Z": 13,\n    "2026-01-12T04:17:00Z": 14,\n    "2026-01-12T04:23:00Z": 15,\n    "2026-01-12T04:28:00Z": 16,\n    "2026-01-12T04:32:00Z": null,\n    "2026-01-12T04:35:00Z": null,\n    "2026-01-12T04:42:00Z": null,\n    "2026-01-12T04:48:00Z": null,\n    "2026-01-12T04:53:00Z": null,\n    "2026-01-12T04:57:00Z": null,\n    "2026-01-12T05:00:00Z": 21,\n    "2026-01-12T05:07:00Z": 20,\n    "2026-01-12T05:13:00Z": 19,\n    "2026-01-12T05:18:00Z": 17,\n    "2026-01-12T05:22:00Z": 16,\n    "2026-01-12T05:25:00Z": 15,\n    "2026-01-12T05:32:00Z": 14,\n    "2026-01-12T05:38:00Z": 13,\n    "2026-01-12T05:43:00Z": 13,\n    "2026-01-12T05:47:00Z": 14,\n    "2026-01-12T05:50:00Z": 15,\n    "2026-01-12T05:57:00Z": 16,\n    "2026-01-12T06:03:00Z": 17,\n    "2026-01-12T06:08:00Z": 18,\n    "2026-01-12T06:12:00Z": 19,\n    "2026-01-12T06:15:00Z": 20,\n    "2026-01-12T06:22:00Z": 21,\n    "2026-01-12T06:28:00Z": 21,\n    "2026-01-12T06:33:00Z": 20,\n    "2026-01-12T06:37:00Z": 19,\n    "2026-01-12T06:40:00Z": 18,\n    "2026-01-12T06:47:00Z": 16,\n    "2026-01-12T06:53:00Z": 15,\n    "2026-01-12T06:58:00Z": 14,\n    "2026-01-12T07:02:00Z": 13,\n    "2026-01-12T07:05:00Z": 12,\n    "2026-01-12T07:12:00Z": 12,\n    "2026-01-12T07:18:00Z": 12,\n    "2026-01-12T07:23:00Z": 13,\n    "2026-01-12T07:27:00Z": 14,\n    "2026-01-12T07:30:00Z": 15,\n    "2026-01-12T07:37:00Z": 17,\n    "2026-01-12T07:43:00Z": 18,\n    "2026-01-12T07:48:00Z": 19,\n    "2026-01-12T07:52:00Z": 19,\n    "2026-01-12T07:55:00Z": 19,\n    "2026-01-12T08:02:00Z": null,\n    "2026-01-12T08:08:00Z": null,\n    "2026-01-12T08:13:00Z": null,\n    "2026-01-12T08:17:00Z": null,\n    "2026-01-12T08:20:00Z": null,\n    "2026-01-12T08:27:00Z": null,\n    "2026-01-12T08:33:00Z": null,\n    "2026-01-12T08:38:00Z": null,\n    "2026-01-12T08:42:00Z": null,\n    "2026-01-12T08:45:00Z": null,\n    "2026-01-12T08:52:00Z": null,\n    "2026-01-12T08:58:00Z": null,\n    "2026-01-12T09:03:00Z": null,\n    "2026-01-12T09:07:00Z": null,\n    "2026-01-12T09:10:00Z": null,\n    "2026-01-12T09:17:00Z": null,\n    "2026-01-12T09:23:00Z": null,\n    "2026-01-12T09:28:00Z": null,\n    "2026-01-12T09:32:00Z": null,\n    "2026-01-12T09:35:00Z": null,\n    "2026-01-12T09:42:00Z": null,\n    "2026-01-12T09:48:00Z": null,\n    "2026-01-12T09:53:00Z": null,\n    "2026-01-12T09:57:00Z": null,\n    "2026-01-12T10:00:00Z": null,\n    "2026-01-12T10:07:00Z": null,\n    "2026-01-12T10:13:00Z": null,\n    "2026-01-12T10:18:00Z": null,\n    "2026-01-12T10:22:00Z": null,\n    "2026-01-12T10:25:00Z": null,\n    "2026-01-12T10:32:00Z": 12,\n    "2026-01-12T10:38:00Z": 13,\n    "2026-01-12T10:43:00Z": 14,\n    "2026-01-12T10:47:00Z": 15,\n    "2026-01-12T10:50:00Z": 15,\n    "2026-01-12T10:57:00Z": 15,\n    "2026-01-12T11:03:00Z": 15,\n    "2026-01-12T11:08:00Z": 14,\n    "2026-01-12T11:12:00Z": 12,\n    "2026-01-12T11:15:00Z": 11,\n    "2026-01-12T11:22:00Z": 9,\n    "2026-01-12T11:28:00Z": 8,\n    "2026-01-12T11:33:00Z": 7,\n    "2026-01-12T11:37:00Z": 6,\n    "2026-01-12T11:40:00Z": null,\n    "2026-01-12T11:47:00Z": null,\n    "2026-01-12T11:53:00Z": 8,\n    "2026-01-12T11:58:00Z": 9,\n    "2026-01-12T12:02:00Z": 10,\n    "2026-01-12T12:05:00Z": 11,\n    "2026-01-12T12:12:00Z": 12,\n    "2026-01-12T12:18:00Z": 13,\n    "2026-01-12T12:23:00Z": 14,\n    "2026-01-12T12:27:00Z": 14,\n    "2026-01-12T12:30:00Z": 13,\n    "2026-01-12T12:37:00Z": 12,\n    "2026-01-12T12:43:00Z": 11,\n    "2026-01-12T12:48:00Z": 9,\n    "2026-01-12T12:52:00Z": 8,\n    "2026-01-12T12:55:00Z": 6,\n    "2026-01-12T13:02:00Z": 5,\n    "2026-01-12T13:08:00Z": 5,\n    "2026-01-12T13:13:00Z": 5,\n    "2026-01-12T13:17:00Z": 5,\n    "2026-01-12T13:20:00Z": 6,\n    "2026-01-12T13:27:00Z": 7,\n    "2026-01-12T13:33:00Z": 8,\n    "2026-01-12T13:38:00Z": 10,\n    "2026-01-12T13:42:00Z": 11,\n    "2026-01-12T13:45:00Z": null,\n    "2026-01-12T13:52:00Z": null,\n    "2026-01-12T13:58:00Z": null,\n    "2026-01-12T14:03:00Z": null,\n    "2026-01-12T14:07:00Z": null,\n    "2026-01-12T14:10:00Z": null,\n    "2026-01-12T14:17:00Z": null,\n    "2026-01-12T14:23:00Z": null,\n    "2026-01-12T14:28:00Z": 5,\n    "2026-01-12T14:32:00Z": 4,\n    "2026-01-12T14:35:00Z": 3,\n    "2026-01-12T14:42:00Z": 3,\n    "2026-01-12T14:48:00Z": 3,\n    "2026-01-12T14:53:00Z": 4,\n    "2026-01-12T14:57:00Z": 5,\n    "2026-01-12T15:00:00Z": 7,\n    "2026-01-12T15:07:00Z": 8,\n    "2026-01-12T15:13:00Z": 9,\n    "2026-01-12T15:18:00Z": 10,\n    "2026-01-12T15:22:00Z": 10,\n    "2026-01-12T15:25:00Z": 10,\n    "2026-01-12T15:32:00Z": 9,\n    "2026-01-12T15:38:00Z": 8,\n    "2026-01-12T15:43:00Z": 7,\n    "2026-01-12T15:47:00Z": 6,\n    "2026-01-12T15:50:00Z": 4,\n    "2026-01-12T15:57:00Z": 3,\n    "2026-01-12T16:03:00Z": 2,\n    "2026-01-12T16:08:00Z": 1,\n    "2026-01-12T16:12:00Z": 1,\n    "2026-01-12T16:15:00Z": 1,\n    "2026-01-12T16:22:00Z": 2,\n    "2026-01-12T16:28:00Z": 3,\n    "2026-01-12T16:33:00Z": 5,\n    "2026-01-12T16:37:00Z": 6,\n    "2026-01-12T16:40:00Z": null,\n    "2026-01-12T16:47:00Z": null,\n    "2026-01-12T16:53:00Z": null,\n    "2026-01-12T16:58:00Z": null,\n    "2026-01-12T17:02:00Z": 7,\n    "2026-01-12T17:05:00Z": 6,\n    "2026-01-12T17:12:00Z": 5,\n    "2026-01-12T17:18:00Z": 4,\n    "2026-01-12T17:23:00Z": 2,\n    "2026-01-12T17:27:00Z": 1,\n    "2026-01-12T17:30:00Z": 0,\n    "2026-01-12T17:37:00Z": -1,\n    "2026-01-12T17:43:00Z": -1,\n    "2026-01-12T17:48:00Z": 0,\n    "2026-01-12T17:52:00Z": 1,\n    "2026-01-12T17:55:00Z": 2,\n    "2026-01-12T18:02:00Z": 3,\n    "2026-01-12T18:08:00Z": 4,\n    "2026-01-12T18:13:00Z": 5,\n    "2026-01-12T18:17:00Z": 6,\n    "2026-01-12T18:20:00Z": null,\n    "2026-01-12T18:27:00Z": null,\n    "2026-01-12T18:33:00Z": null,\n    "2026-01-12T18:38:00Z": null,\n    "2026-01-12T18:42:00Z": null,\n    "2026-01-12T18:45:00Z": null,\n    "2026-01-12T18:52:00Z": null,\n    "2026-01-12T18:58:00Z": null,\n    "2026-01-12T19:03:00Z": null,\n    "2026-01-12T19:07:00Z": -1,\n    "2026-01-12T19:10:00Z": -1,\n    "2026-01-12T19:17:00Z": -1,\n    "2026-01-12T19:23:00Z": 0,\n    "2026-01-12T19:28:00Z": 1,\n    "2026-01-12T19:32:00Z": 2,\n    "2026-01-12T19:35:00Z": 4,\n    "2026-01-12T19:42:00Z": null,\n    "2026-01-12T19:48:00Z": null,\n    "2026-01-12T19:53:00Z": null,\n    "2026-01-12T19:57:00Z": null,\n    "2026-01-12T20:00:00Z": null,\n    "2026-01-12T20:07:00Z": 5,\n    "2026-01-12T20:13:00Z": 4,\n    "2026-01-12T20:18:00Z": 3,\n    "2026-01-12T20:22:00Z": 1,\n    "2026-01-12T20:25:00Z": 0,\n    "2026-01-12T20:32:00Z": 0,\n    "2026-01-12T20:38:00Z": -1,\n    "2026-01-12T20:43:00Z": -1,\n    "2026-01-12T20:47:00Z": 0,\n    "2026-01-12T20:50:00Z": 1,\n    "2026-01-12T20:57:00Z": 2,\n    "2026-01-12T21:03:00Z": 4,\n    "2026-01-12T21:08:00Z": 5,\n    "2026-01-12T21:12:00Z": 6,\n    "2026-01-12T21:15:00Z": 7,\n    "2026-01-12T21:22:00Z": 8,\n    "2026-01-12T21:28:00Z": 8,\n    "2026-01-12T21:33:00Z": 8,\n    "2026-01-12T21:37:00Z": 7,\n    "2026-01-12T21:40:00Z": null,\n    "2026-01-12T21:47:00Z": null,\n    "2026-01-12T21:53:00Z": null,\n    "2026-01-12T21:58:00Z": null,\n    "2026-01-12T22:02:00Z": null,\n    "2026-01-12T22:05:00Z": null,\n    "2026-01-12T22:12:00Z": null,\n    "2026-01-12T22:18:00Z": 2,\n    "2026-01-12T22:23:00Z": 3,\n    "2026-01-12T22:27:00Z": 5,\n    "2026-01-12T22:30:00Z": 6,\n    "2026-01-12T22:37:00Z": 8,\n    "2026-01-12T22:43:00Z": 9,\n    "2026-01-12T22:48:00Z": 10,\n    "2026-01-12T22:52:00Z": 11,\n    "2026-01-12T22:55:00Z": null,\n    "2026-01-12T23:02:00Z": null,\n    "2026-01-12T23:08:00Z": null,\n    "2026-01-12T23:13:00Z": null,\n    "2026-01-12T23:17:00Z": null,\n    "2026-01-12T23:20:00Z": null,\n    "2026-01-12T23:27:00Z": null,\n    "2026-01-12T23:33:00Z": null,\n    "2026-01-12T23:38:00Z": null,\n    "2026-01-12T23:42:00Z": null,\n    "2026-01-12T23:45:00Z": 6,\n    "2026-01-12T23:52:00Z": 7,\n    "2026-01-12T23:58:00Z": 8\n}'
            },
        }
    ]
}

RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "timeseries",
            "filters": {
                "value": '{\n    "2026-01-12T00:00:00Z": 10,\n    "2026-01-12T00:07:00Z": 12,\n    "2026-01-12T00:13:00Z": 13,\n    "2026-01-12T00:18:00Z": 14,\n    "2026-01-12T00:22:00Z": 15,\n    "2026-01-12T00:25:00Z": 15,\n    "2026-01-12T00:32:00Z": 15,\n    "2026-01-12T00:38:00Z": 14,\n    "2026-01-12T00:43:00Z": 13,\n    "2026-01-12T00:47:00Z": 12,\n    "2026-01-12T00:50:00Z": 11,\n    "2026-01-12T00:57:00Z": 10,\n    "2026-01-12T01:03:00Z": null,\n    "2026-01-12T01:08:00Z": 9,\n    "2026-01-12T01:12:00Z": 9,\n    "2026-01-12T01:15:00Z": 10,\n    "2026-01-12T01:22:00Z": 11,\n    "2026-01-12T01:28:00Z": 12,\n    "2026-01-12T01:33:00Z": 14,\n    "2026-01-12T01:37:00Z": 15,\n    "2026-01-12T01:40:00Z": 17,\n    "2026-01-12T01:47:00Z": 18,\n    "2026-01-12T01:53:00Z": 18,\n    "2026-01-12T01:58:00Z": 19,\n    "2026-01-12T02:02:00Z": 18,\n    "2026-01-12T02:05:00Z": 18,\n    "2026-01-12T02:12:00Z": 16,\n    "2026-01-12T02:18:00Z": 15,\n    "2026-01-12T02:23:00Z": 14,\n    "2026-01-12T02:27:00Z": 13,\n    "2026-01-12T02:30:00Z": null,\n    "2026-01-12T02:37:00Z": null,\n    "2026-01-12T02:43:00Z": null,\n    "2026-01-12T02:48:00Z": 13,\n    "2026-01-12T02:52:00Z": 14,\n    "2026-01-12T02:55:00Z": 15,\n    "2026-01-12T03:02:00Z": 16,\n    "2026-01-12T03:08:00Z": 18,\n    "2026-01-12T03:13:00Z": 19,\n    "2026-01-12T03:17:00Z": 20,\n    "2026-01-12T03:20:00Z": 21,\n    "2026-01-12T03:27:00Z": 21,\n    "2026-01-12T03:33:00Z": 20,\n    "2026-01-12T03:38:00Z": 20,\n    "2026-01-12T03:42:00Z": 19,\n    "2026-01-12T03:45:00Z": 17,\n    "2026-01-12T03:52:00Z": 16,\n    "2026-01-12T03:58:00Z": 15,\n    "2026-01-12T04:03:00Z": 14,\n    "2026-01-12T04:07:00Z": 13,\n    "2026-01-12T04:10:00Z": 13,\n    "2026-01-12T04:17:00Z": 14,\n    "2026-01-12T04:23:00Z": 15,\n    "2026-01-12T04:28:00Z": 16,\n    "2026-01-12T04:32:00Z": null,\n    "2026-01-12T04:35:00Z": null,\n    "2026-01-12T04:42:00Z": null,\n    "2026-01-12T04:48:00Z": null,\n    "2026-01-12T04:53:00Z": null,\n    "2026-01-12T04:57:00Z": null,\n    "2026-01-12T05:00:00Z": 21,\n    "2026-01-12T05:07:00Z": 20,\n    "2026-01-12T05:13:00Z": 19,\n    "2026-01-12T05:18:00Z": 17,\n    "2026-01-12T05:22:00Z": 16,\n    "2026-01-12T05:25:00Z": 15,\n    "2026-01-12T05:32:00Z": 14,\n    "2026-01-12T05:38:00Z": 13,\n    "2026-01-12T05:43:00Z": 13,\n    "2026-01-12T05:47:00Z": 14,\n    "2026-01-12T05:50:00Z": 15,\n    "2026-01-12T05:57:00Z": 16,\n    "2026-01-12T06:03:00Z": 17,\n    "2026-01-12T06:08:00Z": 18,\n    "2026-01-12T06:12:00Z": 19,\n    "2026-01-12T06:15:00Z": 20,\n    "2026-01-12T06:22:00Z": 21,\n    "2026-01-12T06:28:00Z": 21,\n    "2026-01-12T06:33:00Z": 20,\n    "2026-01-12T06:37:00Z": 19,\n    "2026-01-12T06:40:00Z": 18,\n    "2026-01-12T06:47:00Z": 16,\n    "2026-01-12T06:53:00Z": 15,\n    "2026-01-12T06:58:00Z": 14,\n    "2026-01-12T07:02:00Z": 13,\n    "2026-01-12T07:05:00Z": 12,\n    "2026-01-12T07:12:00Z": 12,\n    "2026-01-12T07:18:00Z": 12,\n    "2026-01-12T07:23:00Z": 13,\n    "2026-01-12T07:27:00Z": 14,\n    "2026-01-12T07:30:00Z": 15,\n    "2026-01-12T07:37:00Z": 17,\n    "2026-01-12T07:43:00Z": 18,\n    "2026-01-12T07:48:00Z": 19,\n    "2026-01-12T07:52:00Z": 19,\n    "2026-01-12T07:55:00Z": 19,\n    "2026-01-12T08:02:00Z": null,\n    "2026-01-12T08:08:00Z": null,\n    "2026-01-12T08:13:00Z": null,\n    "2026-01-12T08:17:00Z": null,\n    "2026-01-12T08:20:00Z": null,\n    "2026-01-12T08:27:00Z": null,\n    "2026-01-12T08:33:00Z": null,\n    "2026-01-12T08:38:00Z": null,\n    "2026-01-12T08:42:00Z": null,\n    "2026-01-12T08:45:00Z": null,\n    "2026-01-12T08:52:00Z": null,\n    "2026-01-12T08:58:00Z": null,\n    "2026-01-12T09:03:00Z": null,\n    "2026-01-12T09:07:00Z": null,\n    "2026-01-12T09:10:00Z": null,\n    "2026-01-12T09:17:00Z": null,\n    "2026-01-12T09:23:00Z": null,\n    "2026-01-12T09:28:00Z": null,\n    "2026-01-12T09:32:00Z": null,\n    "2026-01-12T09:35:00Z": null,\n    "2026-01-12T09:42:00Z": null,\n    "2026-01-12T09:48:00Z": null,\n    "2026-01-12T09:53:00Z": null,\n    "2026-01-12T09:57:00Z": null,\n    "2026-01-12T10:00:00Z": null,\n    "2026-01-12T10:07:00Z": null,\n    "2026-01-12T10:13:00Z": null,\n    "2026-01-12T10:18:00Z": null,\n    "2026-01-12T10:22:00Z": null,\n    "2026-01-12T10:25:00Z": null,\n    "2026-01-12T10:32:00Z": 12,\n    "2026-01-12T10:38:00Z": 13,\n    "2026-01-12T10:43:00Z": 14,\n    "2026-01-12T10:47:00Z": 15,\n    "2026-01-12T10:50:00Z": 15,\n    "2026-01-12T10:57:00Z": 15,\n    "2026-01-12T11:03:00Z": 15,\n    "2026-01-12T11:08:00Z": 14,\n    "2026-01-12T11:12:00Z": 12,\n    "2026-01-12T11:15:00Z": 11,\n    "2026-01-12T11:22:00Z": 9,\n    "2026-01-12T11:28:00Z": 8,\n    "2026-01-12T11:33:00Z": 7,\n    "2026-01-12T11:37:00Z": 6,\n    "2026-01-12T11:40:00Z": null,\n    "2026-01-12T11:47:00Z": null,\n    "2026-01-12T11:53:00Z": 8,\n    "2026-01-12T11:58:00Z": 9,\n    "2026-01-12T12:02:00Z": 10,\n    "2026-01-12T12:05:00Z": 11,\n    "2026-01-12T12:12:00Z": 12,\n    "2026-01-12T12:18:00Z": 13,\n    "2026-01-12T12:23:00Z": 14,\n    "2026-01-12T12:27:00Z": 14,\n    "2026-01-12T12:30:00Z": 13,\n    "2026-01-12T12:37:00Z": 12,\n    "2026-01-12T12:43:00Z": 11,\n    "2026-01-12T12:48:00Z": 9,\n    "2026-01-12T12:52:00Z": 8,\n    "2026-01-12T12:55:00Z": 6,\n    "2026-01-12T13:02:00Z": 5,\n    "2026-01-12T13:08:00Z": 5,\n    "2026-01-12T13:13:00Z": 5,\n    "2026-01-12T13:17:00Z": 5,\n    "2026-01-12T13:20:00Z": 6,\n    "2026-01-12T13:27:00Z": 7,\n    "2026-01-12T13:33:00Z": 8,\n    "2026-01-12T13:38:00Z": 10,\n    "2026-01-12T13:42:00Z": 11,\n    "2026-01-12T13:45:00Z": null,\n    "2026-01-12T13:52:00Z": null,\n    "2026-01-12T13:58:00Z": null,\n    "2026-01-12T14:03:00Z": null,\n    "2026-01-12T14:07:00Z": null,\n    "2026-01-12T14:10:00Z": null,\n    "2026-01-12T14:17:00Z": null,\n    "2026-01-12T14:23:00Z": null,\n    "2026-01-12T14:28:00Z": 5,\n    "2026-01-12T14:32:00Z": 4,\n    "2026-01-12T14:35:00Z": 3,\n    "2026-01-12T14:42:00Z": 3,\n    "2026-01-12T14:48:00Z": 3,\n    "2026-01-12T14:53:00Z": 4,\n    "2026-01-12T14:57:00Z": 5,\n    "2026-01-12T15:00:00Z": 7,\n    "2026-01-12T15:07:00Z": 8,\n    "2026-01-12T15:13:00Z": 9,\n    "2026-01-12T15:18:00Z": 10,\n    "2026-01-12T15:22:00Z": 10,\n    "2026-01-12T15:25:00Z": 10,\n    "2026-01-12T15:32:00Z": 9,\n    "2026-01-12T15:38:00Z": 8,\n    "2026-01-12T15:43:00Z": 7,\n    "2026-01-12T15:47:00Z": 6,\n    "2026-01-12T15:50:00Z": 4,\n    "2026-01-12T15:57:00Z": 3,\n    "2026-01-12T16:03:00Z": 2,\n    "2026-01-12T16:08:00Z": 1,\n    "2026-01-12T16:12:00Z": 1,\n    "2026-01-12T16:15:00Z": 1,\n    "2026-01-12T16:22:00Z": 2,\n    "2026-01-12T16:28:00Z": 3,\n    "2026-01-12T16:33:00Z": 5,\n    "2026-01-12T16:37:00Z": 6,\n    "2026-01-12T16:40:00Z": null,\n    "2026-01-12T16:47:00Z": null,\n    "2026-01-12T16:53:00Z": null,\n    "2026-01-12T16:58:00Z": null,\n    "2026-01-12T17:02:00Z": 7,\n    "2026-01-12T17:05:00Z": 6,\n    "2026-01-12T17:12:00Z": 5,\n    "2026-01-12T17:18:00Z": 4,\n    "2026-01-12T17:23:00Z": 2,\n    "2026-01-12T17:27:00Z": 1,\n    "2026-01-12T17:30:00Z": 0,\n    "2026-01-12T17:37:00Z": -1,\n    "2026-01-12T17:43:00Z": -1,\n    "2026-01-12T17:48:00Z": 0,\n    "2026-01-12T17:52:00Z": 1,\n    "2026-01-12T17:55:00Z": 2,\n    "2026-01-12T18:02:00Z": 3,\n    "2026-01-12T18:08:00Z": 4,\n    "2026-01-12T18:13:00Z": 5,\n    "2026-01-12T18:17:00Z": 6,\n    "2026-01-12T18:20:00Z": null,\n    "2026-01-12T18:27:00Z": null,\n    "2026-01-12T18:33:00Z": null,\n    "2026-01-12T18:38:00Z": null,\n    "2026-01-12T18:42:00Z": null,\n    "2026-01-12T18:45:00Z": null,\n    "2026-01-12T18:52:00Z": null,\n    "2026-01-12T18:58:00Z": null,\n    "2026-01-12T19:03:00Z": null,\n    "2026-01-12T19:07:00Z": -1,\n    "2026-01-12T19:10:00Z": -1,\n    "2026-01-12T19:17:00Z": -1,\n    "2026-01-12T19:23:00Z": 0,\n    "2026-01-12T19:28:00Z": 1,\n    "2026-01-12T19:32:00Z": 2,\n    "2026-01-12T19:35:00Z": 4,\n    "2026-01-12T19:42:00Z": null,\n    "2026-01-12T19:48:00Z": null,\n    "2026-01-12T19:53:00Z": null,\n    "2026-01-12T19:57:00Z": null,\n    "2026-01-12T20:00:00Z": null,\n    "2026-01-12T20:07:00Z": 5,\n    "2026-01-12T20:13:00Z": 4,\n    "2026-01-12T20:18:00Z": 3,\n    "2026-01-12T20:22:00Z": 1,\n    "2026-01-12T20:25:00Z": 0,\n    "2026-01-12T20:32:00Z": 0,\n    "2026-01-12T20:38:00Z": -1,\n    "2026-01-12T20:43:00Z": -1,\n    "2026-01-12T20:47:00Z": 0,\n    "2026-01-12T20:50:00Z": 1,\n    "2026-01-12T20:57:00Z": 2,\n    "2026-01-12T21:03:00Z": 4,\n    "2026-01-12T21:08:00Z": 5,\n    "2026-01-12T21:12:00Z": 6,\n    "2026-01-12T21:15:00Z": 7,\n    "2026-01-12T21:22:00Z": 8,\n    "2026-01-12T21:28:00Z": 8,\n    "2026-01-12T21:33:00Z": 8,\n    "2026-01-12T21:37:00Z": 7,\n    "2026-01-12T21:40:00Z": null,\n    "2026-01-12T21:47:00Z": null,\n    "2026-01-12T21:53:00Z": null,\n    "2026-01-12T21:58:00Z": null,\n    "2026-01-12T22:02:00Z": null,\n    "2026-01-12T22:05:00Z": null,\n    "2026-01-12T22:12:00Z": null,\n    "2026-01-12T22:18:00Z": 2,\n    "2026-01-12T22:23:00Z": 3,\n    "2026-01-12T22:27:00Z": 5,\n    "2026-01-12T22:30:00Z": 6,\n    "2026-01-12T22:37:00Z": 8,\n    "2026-01-12T22:43:00Z": 9,\n    "2026-01-12T22:48:00Z": 10,\n    "2026-01-12T22:52:00Z": 11,\n    "2026-01-12T22:55:00Z": null,\n    "2026-01-12T23:02:00Z": null,\n    "2026-01-12T23:08:00Z": null,\n    "2026-01-12T23:13:00Z": null,\n    "2026-01-12T23:17:00Z": null,\n    "2026-01-12T23:20:00Z": null,\n    "2026-01-12T23:27:00Z": null,\n    "2026-01-12T23:33:00Z": null,\n    "2026-01-12T23:38:00Z": null,\n    "2026-01-12T23:42:00Z": null,\n    "2026-01-12T23:45:00Z": 6,\n    "2026-01-12T23:52:00Z": 7,\n    "2026-01-12T23:58:00Z": 8\n}'
            },
        }
    ]
}
