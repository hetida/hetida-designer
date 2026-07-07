"""Documentation for Single Timeseries Plot

# Single Timeseries Plot

## Description

Creates an interactive Plotly line chart for a single time series.

## Inputs

* **series** (*Pandas Series*): Timeseries to be plotted. Values must be numeric and the index must be a `DateTimeIndex`.
* **ymin** (*float, optional*): Lower limit of the y-axis. If not specified, the minimum value is determined automatically from the data.
* **ymax** (*float, optional*): Upper limit of the y-axis. If not specified, the maximum value is determined automatically from the data.
* **color** (*string, optional*): Line color of the plotted series. Defaults to `ki.green`. Can be a color hey value like `#89CE6E`. Can also be a named color, e.g. "red" or a fuseki color like "ki.tech".
* **ylabel** (*string, optional*): Label of the y-axis. If not specified (null/None), the metric name and unit are extracted from the series metadata, if available. If that does not yield a non-empty string or ylabel is explicitely set to the string "__OFF__", no yaxis label will be shown.
* **xmin** (*string, optional*): Lower x-axis limit. The value is interpreted using `dtexp`. If not specified, the queried interval from the metadata is used. If no metadata is available, the minimum timestamp of the series is used.
* **xmax** (*string, optional*): Upper x-axis limit. The value is interpreted using `dtexp`. If not specified, the queried interval from the metadata is used. If no metadata is available, the maximum timestamp of the series is used.
* **connection_type** (*string, optional*): Defines how consecutive data points are connected. As default a linear line is drawn between consecutive datapoints. Supported values are:
  * `linear` (default): Straight line segments between points.
  * `forward_steps`: Step plot with horizontal segments followed by vertical transitions.
  * `backward_steps`: Step plot with vertical transitions followed by horizontal segments.
* **maximum_gap_size** (*string, optional*): Maximum allowed time gap between two consecutive data points that are connected by a line. The value must be specified as a pandas frequency string (e.g. `5min`, `1h`, `2d`). Gaps larger than the specified value are visualized as breaks in the line. Per default no check for long gaps between consecutive timestamps is performed.
* **marker_threshold** (integer, optional): Parameter that controls when to add markers to the line plot. By default, markers are displayed until the series length is smaller than 300. In case markers should never be drawn, please define 0. In case markers should always be drawn please define a negative number, .e.g, -1. (Note that this might reduce the processing speed of this component.)
* **locale** (*string, optional*): A plotly locale string like "de", "de-DE" or "en-US". If not explicitely provided (null/None) the locale will be inferred from plot target settings. If explicitely provided using this param this has higher priority.
* **target_timezone** (*string, optional*): If this is not provided, i.e. has its default value null / None, the target timezone will be inferred from plot_target_settings. If it is provided this param has higher priority. Example values: "Europe/Berlin" or "+02:00". See possible timezone strings in pandas’ tz_convert method or pytz all_timezones list

## Outputs

* **plot** (*Plotly JSON*): The generated Plotly figure represented as a JSON object.

## Details

* The component visualizes the input **series** as a Plotly line chart.
* If **ymin** and **ymax** are not specified, the y-axis range is automatically extended by 5% above and below the data range.
* If the series is empty:
  * the x-axis range defaults to `1970-01-01 00:00:00 UTC` to `1970-01-02 00:00:00 UTC`,
  * the y-axis range defaults to `0` to `1`.
* If **maximum_gap_size** is specified, gaps larger than the given threshold are rendered as disconnected line segments.
* **maximum_gap_size** must represent an unambiguous interval that can be converted to a pandas `Timedelta`.
* If NaN exists in consecutive timestamps of **series** a gap is drawn.

## Example

The JSON input of a typical component invocation is:

```json
{
  "__hd_wrapped_data_object__": "SERIES",
  "__metadata__": {
    "dataset_metadata": {
      "ref_interval_start_timestamp": "2026-06-01T22:00:00.000Z",
      "ref_interval_end_timestamp": "2026-06-23T22:00:00.000Z",
      "ref_interval_type": "closed"
    },
    "single_metric_metadata": {
      "structured_metadata": {
        "metric": {
          "name": "Tagesmittelwert",
          "display_name": null,
          "short_display_name": null,
          "description": "Abfluss",
          "unit": "l/s",
          "measurement": null,
          "value_data_type": null,
          "external_id": "precipitation_in_mm_h",
          "signal_id": "ff05d22b-1968-47d2-9683-e7598723cd56"
        },
        "comments": [],
        "inherited": {}
      }
    }
  },
  "__data__": {
    "name": "7485907a-ae39-45c6-a698-e81fbf6d2dda",
    "index": [
      "2026-06-01T22:00:00.000Z",
      "2026-06-02T22:00:00.000Z",
      "2026-06-03T22:00:00.000Z",
      "2026-06-04T22:00:00.000Z",
      "2026-06-05T22:00:00.000Z",
      "2026-06-06T22:00:00.000Z",
      "2026-06-07T22:00:00.000Z",
      "2026-06-08T22:00:00.000Z",
      "2026-06-16T22:00:00.000Z",
      "2026-06-17T22:00:00.000Z",
      "2026-06-18T22:00:00.000Z",
      "2026-06-19T22:00:00.000Z",
      "2026-06-20T22:00:00.000Z",
      "2026-06-21T22:00:00.000Z",
      "2026-06-22T22:00:00.000Z",
      "2026-06-23T22:00:00.000Z"
    ],
    "data": [
      567.8958333333,
      588.36875,
      575.3597222222,
      592.5548611111,
      568.5895104895,
      573.8763888889,
      553.086170952,
      561.0198300283,
      568.2150411281,
      582.1902777778,
      572.9930555556,
      575.7409722222,
      568.7248088951,
      556.4777777778,
      538.7477414871,
      549.191104934
    ]
  },
  "__data_parsing_options__": {
    "orient": "split"
  }
}
```
"""

import json

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import pytest
from dtexp import parse_dtexp
from hdhelpers import (
    get_locale,
    modify_timezone,
    resolve_color,
    set_agnostic_theme,
    set_dt_ticks,
)
from hdhelpers.metadata import get_queried_interval, get_series_name, get_series_unit

from hdutils import plotly_fig_to_json_dict

pio.templates.default = None

DEFAULT_EMPTY_XMIN = None  # pd.Timestamp("1970-01-01 00:00:00", tz="UTC")
DEFAULT_EMPTY_XMAX = None  # pd.Timestamp("1970-01-02 00:00:00", tz="UTC")

DEFAULT_EMPTY_YMIN = 0
DEFAULT_EMPTY_YMAX = 1

Y_AXIS_PADDING = 0.05

CONNECTION_TYPE_MAP = {
    "linear": "linear",
    "forward_steps": "hv",
    "backward_steps": "vh",
}


def get_x_range(
    series: pd.Series, xmin: str | None, xmax: str | None, to_timezone: str | None
) -> tuple[pd.Timestamp | None]:

    requested_xmin, requested_xmax = get_queried_interval(series)

    if xmin is not None:
        xmin_to_use = parse_dtexp(xmin)
    elif requested_xmin is not None:
        xmin_to_use = requested_xmin
    elif not series.empty:
        xmin_to_use = series.index.min()
    else:
        xmin_to_use = DEFAULT_EMPTY_XMIN

    if xmax is not None:
        xmax_to_use = parse_dtexp(xmax)
    elif requested_xmin is not None:
        xmax_to_use = requested_xmax
    elif not series.empty:
        xmax_to_use = series.index.max()
    else:
        xmax_to_use = DEFAULT_EMPTY_XMAX

    return (
        (
            modify_timezone(xmin_to_use, to_timezone=to_timezone)
            if xmin_to_use is not None
            else None
        ),
        (
            modify_timezone(xmax_to_use, to_timezone=to_timezone)
            if xmax_to_use is not None
            else None
        ),
    )


def get_y_range(
    series: pd.Series, ymin: float | None, ymax: float | None
) -> tuple[float]:

    data_min = series.min()
    data_max = series.max()
    delta = data_max - data_min

    if ymin is not None:
        ymin_to_use = ymin
    elif not series.empty:
        ymin_to_use = data_min - delta * Y_AXIS_PADDING
    else:
        ymin_to_use = DEFAULT_EMPTY_YMIN

    if ymax is not None:
        ymax_to_use = ymax
    elif not series.empty:
        ymax_to_use = data_max + delta * Y_AXIS_PADDING
    else:
        ymax_to_use = DEFAULT_EMPTY_YMAX

    return ymin_to_use, ymax_to_use


def apply_maximum_gap_size(
    series: pd.Series, maximum_gap_size: str | None
) -> pd.Series:

    if maximum_gap_size is None or series.empty:
        return series

    gap_size = abs(series.index.diff(-1).total_seconds())
    max_gap_size = pd.Timedelta(maximum_gap_size).total_seconds()
    entries_to_avoid_connection = series.index[gap_size > max_gap_size] + pd.Timedelta(
        seconds=max(max_gap_size - 0.01, 0)
    )

    nan_series = pd.Series(
        [np.nan] * len(entries_to_avoid_connection), index=entries_to_avoid_connection
    )

    return series.combine_first(nan_series)


def get_y_title(series: pd.Series, ylabel: str | None) -> str:

    if ylabel is not None:
        if ylabel == "__OFF__":
            return ""
        return ylabel

    name = get_series_name(series)
    unit = get_series_unit(series)

    if name is not None and unit is not None:
        return name + f" [{unit}]"
    if name is not None:
        return name
    return ""


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "series": {"data_type": "SERIES"},
        "ymin": {"data_type": "FLOAT", "default_value": None},
        "ymax": {"data_type": "FLOAT", "default_value": None},
        "color": {"data_type": "STRING", "default_value": "ki.green"},
        "ylabel": {"data_type": "STRING", "default_value": None},
        "xmin": {"data_type": "STRING", "default_value": None},
        "xmax": {"data_type": "STRING", "default_value": None},
        "connection_type": {"data_type": "STRING", "default_value": "linear"},
        "maximum_gap_size": {"data_type": "STRING", "default_value": None},
        "marker_threshold": {"data_type": "INT", "default_value": 300},
        "locale": {"data_type": "STRING", "default_value": None},
        "target_timezone": {"data_type": "STRING", "default_value": None},
    },
    "outputs": {
        "plot": {"data_type": "PLOTLYJSON"},
    },
    "name": "Single Timeseries Plot",
    "category": "Visualization",
    "description": "Plotting a single timeseries",
    "version_tag": "1.0.1",
    "id": "d180674a-41af-4f67-aee3-c4c037ccc6b3",
    "revision_group_id": "8fba9b51-a0f1-6c6c-a6d4-e224103b819c",
    "state": "RELEASED",
    "released_timestamp": "2026-06-25T12:15:25.419404+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(
    *,
    series,
    ymin=None,
    ymax=None,
    color="ki.green",
    ylabel=None,
    xmin=None,
    xmax=None,
    connection_type="linear",
    maximum_gap_size=None,
    marker_threshold=300,
    locale=None,
    target_timezone=None,
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    xmin_to_use, xmax_to_use = get_x_range(
        series=series, xmin=xmin, xmax=xmax, to_timezone=target_timezone
    )
    ymin_to_use, ymax_to_use = get_y_range(series=series, ymin=ymin, ymax=ymax)
    ytitle = get_y_title(series=series, ylabel=ylabel)

    series_with_gaps = apply_maximum_gap_size(
        series=series, maximum_gap_size=maximum_gap_size
    )

    # timezone handling for series
    series_with_tz = modify_timezone(series_with_gaps)

    mode = "lines" if 0 <= marker_threshold < len(series) else "lines+markers"
    shape = CONNECTION_TYPE_MAP.get(connection_type, "linear")
    fig = go.Figure(
        [
            go.Scatter(
                x=series_with_tz.index, y=series_with_tz, mode=mode, connectgaps=False
            )
        ]
    )

    fig.update_traces(
        {
            "line_color": resolve_color(color),
            "line_width": 1,
            "line_dash": "solid",
            "line_shape": shape,
            "cliponaxis": False,
        }
    )
    fig.update_yaxes(automargin=True, range=[ymin_to_use, ymax_to_use])

    if xmin_to_use is not None or xmax_to_use is not None:
        fig.update_xaxes(range=[xmin_to_use, xmax_to_use])
    fig.update_xaxes(automargin=True, type="date")

    set_dt_ticks(fig)

    fig.update_layout(
        {
            "autosize": True,
            "height": 200,
            "yaxis_title": None if not ytitle else {"text": ytitle, "standoff": 20},
            "margin": {"l": 0, "r": 5, "b": 0, "t": 5, "pad": 0},
        }
    )

    set_agnostic_theme(fig)

    json_to_return = plotly_fig_to_json_dict(fig)

    plot_target_locale = get_locale(locale)
    json_to_return["config"] = {"displaylogo": False, "showTips": False}

    # set locale if available
    if plot_target_locale is not None:
        json_to_return["config"]["locale"] = plot_target_locale

    return {"plot": json_to_return}


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "series",
            "filters": {
                "value": '{\n  "__hd_wrapped_data_object__": "SERIES",\n  "__metadata__": {\n    "dataset_metadata": {\n      "ref_interval_start_timestamp": "2026-06-01T22:00:00.000Z",\n      "ref_interval_end_timestamp": "2026-06-23T22:00:00.000Z",\n      "ref_interval_type": "closed"\n    },\n    "single_metric_metadata": {\n      "structured_metadata": {\n        "metric": {\n          "name": "Tagesmittelwert",\n          "display_name": null,\n          "short_display_name": null,\n          "description": "Abfluss",\n          "unit": "l/s",\n          "measurement": null,\n          "value_data_type": null,\n          "external_id": "precipitation_in_mm_h",\n          "signal_id": "ff05d22b-1968-47d2-9683-e7598723cd56"\n        },\n        "comments": [],\n        "inherited": {}\n      }\n    }\n  },\n  "__data__": {\n    "name": "7485907a-ae39-45c6-a698-e81fbf6d2dda",\n    "index": [\n      "2026-06-01T22:00:00.000Z",\n      "2026-06-02T22:00:00.000Z",\n      "2026-06-03T22:00:00.000Z",\n      "2026-06-04T22:00:00.000Z",\n      "2026-06-05T22:00:00.000Z",\n      "2026-06-06T22:00:00.000Z",\n      "2026-06-07T22:00:00.000Z",\n      "2026-06-08T22:00:00.000Z",\n      "2026-06-16T22:00:00.000Z",\n      "2026-06-17T22:00:00.000Z",\n      "2026-06-18T22:00:00.000Z",\n      "2026-06-19T22:00:00.000Z",\n      "2026-06-20T22:00:00.000Z",\n      "2026-06-21T22:00:00.000Z",\n      "2026-06-22T22:00:00.000Z",\n      "2026-06-23T22:00:00.000Z"\n    ],\n    "data": [\n      567.8958333333,\n      588.36875,\n      575.3597222222,\n      592.5548611111,\n      568.5895104895,\n      573.8763888889,\n      553.086170952,\n      561.0198300283,\n      568.2150411281,\n      582.1902777778,\n      572.9930555556,\n      575.7409722222,\n      568.7248088951,\n      556.4777777778,\n      538.7477414871,\n      549.191104934\n    ]\n  },\n  "__data_parsing_options__": {\n    "orient": "split"\n  }\n}'
            },
        },
        {
            "workflow_input_name": "ymin",
            "use_default_value": True,
            "filters": {"value": ""},
        },
        {
            "workflow_input_name": "ymax",
            "use_default_value": True,
            "filters": {"value": ""},
        },
        {
            "workflow_input_name": "color",
            "use_default_value": True,
            "filters": {"value": "ki.green"},
        },
        {
            "workflow_input_name": "ylabel",
            "use_default_value": True,
            "filters": {"value": ""},
        },
        {
            "workflow_input_name": "xmin",
            "use_default_value": True,
            "filters": {"value": ""},
        },
        {
            "workflow_input_name": "xmax",
            "use_default_value": True,
            "filters": {"value": ""},
        },
        {
            "workflow_input_name": "connection_type",
            "use_default_value": True,
            "filters": {"value": "linear"},
        },
        {
            "workflow_input_name": "maximum_gap_size",
            "use_default_value": True,
            "filters": {"value": ""},
        },
        {
            "workflow_input_name": "marker_threshold",
            "use_default_value": True,
            "filters": {"value": "300"},
        },
        {
            "workflow_input_name": "locale",
            "use_default_value": True,
            "filters": {"value": ""},
        },
        {
            "workflow_input_name": "target_timezone",
            "use_default_value": True,
            "filters": {"value": ""},
        },
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "series",
            "filters": {
                "value": '{\n  "__hd_wrapped_data_object__": "SERIES",\n  "__metadata__": {\n    "dataset_metadata": {\n      "ref_interval_start_timestamp": "2026-06-01T22:00:00.000Z",\n      "ref_interval_end_timestamp": "2026-06-23T22:00:00.000Z",\n      "ref_interval_type": "closed"\n    },\n    "single_metric_metadata": {\n      "structured_metadata": {\n        "metric": {\n          "name": "Tagesmittelwert",\n          "display_name": null,\n          "short_display_name": null,\n          "description": "Abfluss",\n          "unit": "l/s",\n          "measurement": null,\n          "value_data_type": null,\n          "external_id": "precipitation_in_mm_h",\n          "signal_id": "ff05d22b-1968-47d2-9683-e7598723cd56"\n        },\n        "comments": [],\n        "inherited": {}\n      }\n    }\n  },\n  "__data__": {\n    "name": "7485907a-ae39-45c6-a698-e81fbf6d2dda",\n    "index": [\n      "2026-06-01T22:00:00.000Z",\n      "2026-06-02T22:00:00.000Z",\n      "2026-06-03T22:00:00.000Z",\n      "2026-06-04T22:00:00.000Z",\n      "2026-06-05T22:00:00.000Z",\n      "2026-06-06T22:00:00.000Z",\n      "2026-06-07T22:00:00.000Z",\n      "2026-06-08T22:00:00.000Z",\n      "2026-06-16T22:00:00.000Z",\n      "2026-06-17T22:00:00.000Z",\n      "2026-06-18T22:00:00.000Z",\n      "2026-06-19T22:00:00.000Z",\n      "2026-06-20T22:00:00.000Z",\n      "2026-06-21T22:00:00.000Z",\n      "2026-06-22T22:00:00.000Z",\n      "2026-06-23T22:00:00.000Z"\n    ],\n    "data": [\n      567.8958333333,\n      588.36875,\n      575.3597222222,\n      592.5548611111,\n      568.5895104895,\n      573.8763888889,\n      553.086170952,\n      561.0198300283,\n      568.2150411281,\n      582.1902777778,\n      572.9930555556,\n      575.7409722222,\n      568.7248088951,\n      556.4777777778,\n      538.7477414871,\n      549.191104934\n    ]\n  },\n  "__data_parsing_options__": {\n    "orient": "split"\n  }\n}'
            },
        },
        {
            "workflow_input_name": "ymin",
            "use_default_value": True,
            "filters": {"value": ""},
        },
        {
            "workflow_input_name": "ymax",
            "use_default_value": True,
            "filters": {"value": ""},
        },
        {
            "workflow_input_name": "color",
            "use_default_value": True,
            "filters": {"value": "ki.green"},
        },
        {
            "workflow_input_name": "ylabel",
            "use_default_value": True,
            "filters": {"value": ""},
        },
        {
            "workflow_input_name": "xmin",
            "use_default_value": True,
            "filters": {"value": ""},
        },
        {
            "workflow_input_name": "xmax",
            "use_default_value": True,
            "filters": {"value": ""},
        },
        {
            "workflow_input_name": "connection_type",
            "use_default_value": True,
            "filters": {"value": "linear"},
        },
        {
            "workflow_input_name": "maximum_gap_size",
            "use_default_value": True,
            "filters": {"value": ""},
        },
        {
            "workflow_input_name": "marker_threshold",
            "use_default_value": True,
            "filters": {"value": "300"},
        },
        {
            "workflow_input_name": "locale",
            "use_default_value": True,
            "filters": {"value": ""},
        },
        {
            "workflow_input_name": "target_timezone",
            "use_default_value": True,
            "filters": {"value": ""},
        },
    ]
}


def result_is_valid_json(data):
    try:
        json.dumps(data["plot"])
        return True
    except json.JSONDecodeError:
        return False


def test_empty_series():
    result = main(series=pd.Series())
    assert result_is_valid_json(result)  # noqa: S101


@pytest.mark.parametrize(
    ("optional_arguments"),
    [
        pytest.param({"ymin": -1}, id="only ymin"),
        pytest.param({"ymin": -1, "ymax": 2}, id="ymin+ymax"),
        pytest.param({"color": "green"}, id="color is name"),
        pytest.param({"color": "#F54927"}, id="color is hex"),
        pytest.param({"xmin": "now-1d"}, id="only xmin"),
        pytest.param({"xmin": "now-1d", "xmax": "now+1d"}, id="xmin and xmax"),
        pytest.param({"connection_type": "backward_steps"}, id="connection_type"),
        pytest.param({"maximum_gap_size": "5min"}, id="maximum_gap_size"),
    ],
)
def test_using_keywords_no_metadata(optional_arguments):
    rng = np.random.default_rng(seed=42)
    length = 100
    dates = pd.date_range("2024-01-01", periods=length * 10, freq="1min")[
        rng.choice(length * 10, size=length, replace=False)
    ]
    series = pd.Series(rng.random(length), index=dates)

    result = main(series=series, **optional_arguments)
    assert result_is_valid_json(result)  # noqa S101
