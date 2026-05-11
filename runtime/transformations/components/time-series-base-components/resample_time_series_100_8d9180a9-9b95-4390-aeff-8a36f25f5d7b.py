"""Documentation for Resample Time Series

# Resample Time Series

## Description
Component to bring a time series onto a target time grid. It supports regular
aggregation for downsampling and `asfreq` for pure reindexing without filling
missing values.

## Inputs
- **timeseries** (Pandas Series):
    The input time series. The index must contain timestamps, and the values
    must be numeric.
- **target_frequency** (String):
    Target time frequency such as `5min`, `15min`, `1h`, or `1D`.
    Only fixed timedelta-like frequencies are supported.
- **aggregation_method** (String, default value: "mean"):
    Resampling method. Must be one of `mean`, `median`, `min`, `max`, `sum`,
    or `asfreq`.
    - `mean`, `median`, `min`, `max`, `sum`: aggregate values inside each
      target interval.
    - `asfreq`: only place the series on the target grid. No aggregation and
      no filling is performed. New timestamps stay `NaN` if no original value
      exists there.
- **label_position** (String, default value: "left"):
    Determines whether interval-based results are labeled with the left or the
    right boundary of the resampling interval. Must be one of `left` or
    `right`. For `aggregation_method="asfreq"`, this setting is normally not
    the deciding factor.
- **closed** (String, default value: "left"):
    Determines which side of each interval is closed for interval-based
    resampling. Must be one of `left` or `right`. For
    `aggregation_method="asfreq"`, this setting is normally not the deciding
    factor.

## Outputs
- **resampled_timeseries** (Pandas Series):
    The resampled time series.

## Details
1. The input series is sorted by time and duplicate timestamps are merged by mean.
2. The target frequency is validated as a fixed timedelta-like frequency.
3. For `aggregation_method="asfreq"`, the series is only aligned to the new
   grid and no values are filled.
4. For all other aggregation methods, pandas resampling is used with the chosen
   interval labeling and interval closure.
5. The component returns only the resampled series.
6. If missing values created by resampling should be filled afterwards, use
   `handle_gaps_and_missing_data` as the next component.

## Example
```json
{
  "timeseries": {
    "2026-03-01T00:00:00Z": 1.0,
    "2026-03-01T00:05:00Z": 2.0,
    "2026-03-01T00:10:00Z": 3.0,
    "2026-03-01T00:15:00Z": 4.0,
    "2026-03-01T00:20:00Z": 5.0,
    "2026-03-01T00:25:00Z": 6.0,
    "2026-03-01T00:30:00Z": 7.0
  },
  "target_frequency": "15min",
  "aggregation_method": "mean",
  "label_position": "left",
  "closed": "left"
}
```

Expected output:
```json
{
  "resampled_timeseries": {
    "2026-03-01T00:00:00Z": 2.0,
    "2026-03-01T00:15:00Z": 5.0,
    "2026-03-01T00:30:00Z": 7.0
  }
}
```

Second example with `asfreq`:
```json
{
  "timeseries": {
    "2026-03-01T00:00:00Z": 10.0,
    "2026-03-01T00:10:00Z": 12.0,
    "2026-03-01T00:20:00Z": 14.0
  },
  "target_frequency": "5min",
  "aggregation_method": "asfreq",
  "label_position": "left",
  "closed": "left"
}
```

Expected output:
```json
{
  "resampled_timeseries": {
    "2026-03-01T00:00:00Z": 10.0,
    "2026-03-01T00:05:00Z": null,
    "2026-03-01T00:10:00Z": 12.0,
    "2026-03-01T00:15:00Z": null,
    "2026-03-01T00:20:00Z": 14.0
  }
}
```
"""

from __future__ import annotations

import pandas as pd

from hdutils import ComponentInputValidationException, parse_default_value

AGGREGATION_FUNCTIONS = {
    "mean": "mean",
    "median": "median",
    "min": "min",
    "max": "max",
    "sum": "sum",
    "asfreq": "asfreq",
}


def parse_fixed_frequency(value: str, input_name: str) -> str:
    try:
        offset = pd.tseries.frequencies.to_offset(value)
    except ValueError as exc:
        raise ComponentInputValidationException(
            f"{input_name} must be a valid fixed timedelta string like '5min', '1h', or '1D'",
            error_code="422",
            invalid_component_inputs=[input_name],
        ) from exc

    try:
        _ = offset.nanos
    except ValueError as exc:
        raise ComponentInputValidationException(
            f"{input_name} must be a fixed timedelta string like '5min', '1h', or '1D'",
            error_code="422",
            invalid_component_inputs=[input_name],
        ) from exc

    return value


def validate_inputs(
    timeseries: pd.Series,
    target_frequency: str,
    aggregation_method: str,
    label_position: str,
    closed: str,
) -> str:
    if not isinstance(timeseries, pd.Series):
        raise ComponentInputValidationException(
            "timeseries must be a pandas Series",
            error_code="422",
            invalid_component_inputs=["timeseries"],
        )
    if timeseries.empty:
        raise ComponentInputValidationException(
            "timeseries must not be empty",
            error_code="422",
            invalid_component_inputs=["timeseries"],
        )
    if not isinstance(timeseries.index, pd.DatetimeIndex):
        raise ComponentInputValidationException(
            "timeseries index must be a pandas DatetimeIndex",
            error_code="422",
            invalid_component_inputs=["timeseries"],
        )
    if not pd.api.types.is_numeric_dtype(timeseries):
        raise ComponentInputValidationException(
            "timeseries values must be numeric",
            error_code="422",
            invalid_component_inputs=["timeseries"],
        )

    if aggregation_method not in AGGREGATION_FUNCTIONS:
        raise ComponentInputValidationException(
            f"aggregation_method must be one of {sorted(AGGREGATION_FUNCTIONS)}",
            error_code="422",
            invalid_component_inputs=["aggregation_method"],
        )

    if label_position not in {"left", "right"}:
        raise ComponentInputValidationException(
            "label_position must be one of 'left' or 'right'",
            error_code="422",
            invalid_component_inputs=["label_position"],
        )

    if closed not in {"left", "right"}:
        raise ComponentInputValidationException(
            "closed must be one of 'left' or 'right'",
            error_code="422",
            invalid_component_inputs=["closed"],
        )

    return parse_fixed_frequency(target_frequency, "target_frequency")


def prepare_series(timeseries: pd.Series) -> pd.Series:
    prepared = timeseries.sort_index()
    if not prepared.index.is_unique:
        prepared = prepared.groupby(level=0).mean()
    return prepared


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "timeseries": {"data_type": "SERIES"},
        "target_frequency": {"data_type": "STRING"},
        "aggregation_method": {"data_type": "STRING", "default_value": "mean"},
        "label_position": {"data_type": "STRING", "default_value": "left"},
        "closed": {"data_type": "STRING", "default_value": "left"},
    },
    "outputs": {
        "resampled_timeseries": {"data_type": "SERIES"},
    },
    "name": "Resample Time Series",
    "category": "Time Series Base Components",
    "description": "Bring a time series onto a target time grid.",
    "version_tag": "1.0.0",
    "id": "8d9180a9-9b95-4390-aeff-8a36f25f5d7b",
    "revision_group_id": "b4aa144e-cdfe-4ff5-8337-a5b8e35c1f15",
    "state": "RELEASED",
    "released_timestamp": "2026-05-11T08:00:00+02:00",
}


def main(
    *,
    timeseries,
    target_frequency,
    aggregation_method=parse_default_value(COMPONENT_INFO, "aggregation_method"),
    label_position=parse_default_value(COMPONENT_INFO, "label_position"),
    closed=parse_default_value(COMPONENT_INFO, "closed"),
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # Step 1: Validate inputs and the target frequency.
    target_frequency = validate_inputs(
        timeseries,
        target_frequency,
        aggregation_method,
        label_position,
        closed,
    )

    # Step 2: Sort the series and merge duplicate timestamps by mean.
    prepared = prepare_series(timeseries)

    # Step 3: Resample either by pure reindexing or by interval aggregation.
    resampler = prepared.resample(
        target_frequency,
        label=label_position,
        closed=closed,
    )
    if aggregation_method == "asfreq":
        result = resampler.asfreq()
    else:
        result = resampler.agg(AGGREGATION_FUNCTIONS[aggregation_method])

    # Step 4: Return the resampled series.
    return {
        "resampled_timeseries": result,
    }


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "timeseries",
            "filters": {
                "value": '{\n    "2026-03-01T00:00:00Z": 1.0,\n    "2026-03-01T00:05:00Z": 2.0,\n    "2026-03-01T00:10:00Z": 3.0,\n    "2026-03-01T00:15:00Z": 4.0,\n    "2026-03-01T00:20:00Z": 5.0,\n    "2026-03-01T00:25:00Z": 6.0,\n    "2026-03-01T00:30:00Z": 7.0\n}'
            },
        },
        {"workflow_input_name": "target_frequency", "filters": {"value": "15min"}},
    ]
}

RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "timeseries",
            "filters": {
                "value": '{\n    "2026-03-01T00:00:00Z": 1.0,\n    "2026-03-01T00:05:00Z": 2.0,\n    "2026-03-01T00:10:00Z": 3.0,\n    "2026-03-01T00:15:00Z": 4.0,\n    "2026-03-01T00:20:00Z": 5.0,\n    "2026-03-01T00:25:00Z": 6.0,\n    "2026-03-01T00:30:00Z": 7.0\n}'
            },
        },
        {"workflow_input_name": "target_frequency", "filters": {"value": "15min"}},
    ]
}
