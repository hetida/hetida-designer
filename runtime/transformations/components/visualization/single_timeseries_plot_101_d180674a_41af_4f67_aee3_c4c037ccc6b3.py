"""Documentation for Single Timeseries Plot

# Single Timeseries Plot

## Description

Creates an interactive Plotly line chart for a single time series.

## Inputs

* **series** (*Pandas Series*): Time series to be plotted. Values must be numeric and the index must be a `DateTimeIndex`.
* **ymin** (*float, optional*): Lower limit of the y-axis. If not specified, the minimum value is determined automatically from the data.
* **ymax** (*float, optional*): Upper limit of the y-axis. If not specified, the maximum value is determined automatically from the data.
* **colour** (*string, optional*): Line color of the plotted series. Defaults to `#89CE6E` (light green).
* **ylabel** (*string, optional*): Label of the y-axis. If not specified, the metric name and unit are extracted from the series metadata, if available.
* **xmin** (*string, optional*): Lower x-axis limit. The value is interpreted using `dtexp`. If not specified, the queried interval from the metadata is used. If no metadata is available, the minimum timestamp of the series is used.
* **xmax** (*string, optional*): Upper x-axis limit. The value is interpreted using `dtexp`. If not specified, the queried interval from the metadata is used. If no metadata is available, the maximum timestamp of the series is used.
* **connection_type** (*string, optional*): Defines how consecutive data points are connected. Supported values are:
  * `linear` (default): Straight line segments between points.
  * `forward_steps`: Step plot with horizontal segments followed by vertical transitions.
  * `backward_steps`: Step plot with vertical transitions followed by horizontal segments.
* **maximum_gap_size** (*string, optional*): Maximum allowed time gap between two consecutive data points that are connected by a line. The value must be specified as a pandas frequency string (e.g. `5min`, `1h`, `2d`). Gaps larger than the specified value are visualized as breaks in the line.

## Outputs

* **plot** (*Plotly JSON*): The generated Plotly figure represented as a JSON object.

## Details

* The component visualizes the input **series** as a Plotly line chart.
* By default, markers are displayed in addition to the line.
* For performance reasons, markers are omitted when the series contains more than 300 data points.
* If **ymin** and **ymax** are not specified, the y-axis range is automatically extended by 5% above and below the data range.
* If the series is empty:
  * the x-axis range defaults to `1970-01-01 00:00:00 UTC` to `1970-01-02 00:00:00 UTC`,
  * the y-axis range defaults to `0` to `1`.
* If **maximum_gap_size** is specified, gaps larger than the given threshold are rendered as disconnected line segments.
* **maximum_gap_size** must represent an unambiguous interval that can be converted to a pandas `Timedelta`.

## Example

The JSON input of a typical component invocation is:

```json
{
  "series": {
    "__hd_wrapped_data_object__": "SERIES",
    "__metadata__": {
      "dataset_metadata": {
        "ref_interval_start_timestamp": "2019-11-30T09:00:00.000Z",
        "ref_interval_end_timestamp": "2019-11-30T13:00:00.000Z",
        "ref_interval_type": "closed"
      },
      "single_metric_metadata": {
        "structured_metadata": {
          "metric": {
            "name": "Aktueller Niederschlag",
            "description": "Aktuelle mittlere Niederschlagsrate.",
            "unit": "mm/h",
            "external_id": "precipitation_in_mmh",
            "signal_id": "ff05d22b-1968-47d2-9683-e7598723cd56"
          }
        }
      }
    },
    "__data__": {
      "2019-11-30T09:00:00.000Z": 0,
      "2019-11-30T10:00:00.000Z": 1,
      "2019-11-30T11:00:00.000Z": 0
    }
  },
  "__data_parsing_options__": {
    "orient": "split"
  }
}
```
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from dtexp import parse_dtexp
from hdhelpers.helpers import modify_timezone
from hdhelpers.metadata import get_queried_interval, get_series_name, get_series_unit
from hdhelpers.plot_target_settings import get_plot_target_settings

from hdutils import plotly_fig_to_json_dict

pio.templates.default = None

DEFAULT_EMPTY_XMIN = pd.Timestamp("1970-01-01 00:00:00", tz="UTC")
DEFAULT_EMPTY_XMAX = pd.Timestamp("1970-01-02 00:00:00", tz="UTC")

DEFAULT_EMPTY_YMIN = 0
DEFAULT_EMPTY_YMAX = 1

Y_AXIS_PADDING = 0.05
MARKER_THRESHOLD = 300

CONNECTION_TYPE_MAP = {
    "linear": "linear",
    "forward_steps": "hv",
    "backward_steps": "vh",
}


def get_x_range(series: pd.Series, xmin: str | None, xmax: str | None) -> tuple[pd.Timestamp]:

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

    return modify_timezone(xmin_to_use), modify_timezone(xmax_to_use)


def get_y_range(series: pd.Series, ymin: float | None, ymax: float | None) -> tuple[float]:

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


def apply_maximum_gap_size(series: pd.Series, maximum_gap_size: str | None) -> pd.Series:

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
        "colour": {"data_type": "STRING", "default_value": "#89CE6E"},
        "ylabel": {"data_type": "STRING", "default_value": None},
        "xmin": {"data_type": "STRING", "default_value": None},
        "xmax": {"data_type": "STRING", "default_value": None},
        "connection_type": {"data_type": "STRING", "default_value": "linear"},
        "maximum_gap_size": {"data_type": "STRING", "default_value": None},
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
    "released_timestamp": "2026-06-23T11:18:44.024111+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(
    *,
    series,
    ymin=None,
    ymax=None,
    colour="#89CE6E",
    ylabel=None,
    xmin=None,
    xmax=None,
    connection_type="linear",
    maximum_gap_size=None,
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    xmin_to_use, xmax_to_use = get_x_range(series=series, xmin=xmin, xmax=xmax)
    ymin_to_use, ymax_to_use = get_y_range(series=series, ymin=ymin, ymax=ymax)
    ytitle = get_y_title(series=series, ylabel=ylabel)

    series_with_gaps = apply_maximum_gap_size(series=series, maximum_gap_size=maximum_gap_size)

    # timezone handling for series
    series_with_tz = modify_timezone(series_with_gaps)

    # first plotting version
    mode = "lines" if len(series) > MARKER_THRESHOLD else "lines+markers"
    shape = CONNECTION_TYPE_MAP.get(connection_type, "linear")
    fig = go.Figure(
        [go.Scatter(x=series_with_tz.index, y=series_with_tz, mode=mode, connectgaps=False)]
    )

    fig.update_traces(
        {"line_color": colour, "line_width": 1, "line_dash": "solid", "line_shape": shape}
    )
    fig.update_yaxes(automargin=True, range=[ymin_to_use, ymax_to_use])
    fig.update_xaxes(automargin=True, range=[xmin_to_use, xmax_to_use], type="date")

    fig.update_layout(
        {
            "autosize": True,
            "height": 200,
            "yaxis_title": ytitle,
            "margin": {"l": 0, "r": 0, "b": 0, "t": 5, "pad": 0},
        }
    )

    json_to_return = plotly_fig_to_json_dict(fig)

    # set locale if available
    plot_target_locale = get_plot_target_settings().plot_target_locale
    if plot_target_locale is not None:
        json_to_return["config"] = {"locale": plot_target_locale}

    return {"plot": json_to_return}


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "series",
            "filters": {
                "value": '{\n  "__hd_wrapped_data_object__": "SERIES",\n  "__metadata__": {\n    "dataset_metadata": {\n      "ref_interval_start_timestamp": "2019-11-30T09:00:00.000Z",\n      "ref_interval_end_timestamp": "2019-11-30T13:00:00.000Z",\n      "ref_interval_type": "closed"\n    },\n    "single_metric_metadata": {\n      "structured_metadata": {\n        "metric": {\n          "name": "Aktueller Niederschlag",\n          "display_name": null,\n          "short_display_name": null,\n          "description": "Aktuelle mittlere Niederschlagsrate",\n          "unit": "mm/h",\n          "measurement": null,\n          "value_data_type": null,\n          "external_id": "precipitation_in_mm_h",\n          "signal_id": "ff05d22b-1968-47d2-9683-e7598723cd56"\n        },\n        "comments": [],\n        "inherited": {}\n      }\n    }\n  },\n  "__data__": {\n      "name": "test",\n      "index": ["2019-11-30T09:00:00.000Z", "2019-11-30T10:00:00.000Z",   "2019-11-30T11:00:00.000Z"],\n      "data": [0,1,0]\n  },\n  "__data_parsing_options__": {\n    "orient": "split"\n  }\n}'
            },
        }
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "series",
            "filters": {
                "value": '{\n  "__hd_wrapped_data_object__": "SERIES",\n  "__metadata__": {\n    "dataset_metadata": {\n      "ref_interval_start_timestamp": "2019-11-30T09:00:00.000Z",\n      "ref_interval_end_timestamp": "2019-11-30T13:00:00.000Z",\n      "ref_interval_type": "closed"\n    },\n    "single_metric_metadata": {\n      "structured_metadata": {\n        "metric": {\n          "name": "Aktueller Niederschlag",\n          "display_name": null,\n          "short_display_name": null,\n          "description": "Aktuelle mittlere Niederschlagsrate",\n          "unit": "mm/h",\n          "measurement": null,\n          "value_data_type": null,\n          "external_id": "precipitation_in_mm_h",\n          "signal_id": "ff05d22b-1968-47d2-9683-e7598723cd56"\n        },\n        "comments": [],\n        "inherited": {}\n      }\n    }\n  },\n  "__data__": {\n      "name": "test",\n      "index": ["2019-11-30T09:00:00.000Z", "2019-11-30T10:00:00.000Z",   "2019-11-30T11:00:00.000Z"],\n      "data": [0,1,0]\n  },\n  "__data_parsing_options__": {\n    "orient": "split"\n  }\n}'
            },
        }
    ]
}


try:
    import json
    import pytest
except ModuleNotFoundError:
    pass
else:

    def result_is_json(data):
        try:
            json.loads(data["plot"])
            return True
            except json.JSONDecodeError:
        return False

    def test_empty_series():
        result = main(series=pd.Series())
        assert result_is_json(result)


    @pytest.mark.parametrize(
        ("optional_arguments"),
        [
            pytest.param({"ymin": -1}, id="only ymin"),
            pytest.param({"ymin": -1, "ymax":2}, id="ymin+ymax"),
            pytest.param({"colour": "green"}, id="color is name"),
            pytest.param({"colour": "#F54927"}, id="color is hex"),
            pytest.param({"xmin": "now-1d"}, id="only xmin"),
            pytest.param({"xmin": "now-1d", "xmax": "now+1d"}, id="xmin and xmax"),
            pytest.param({"connection_type": "backward_steps"}, id="connection_type"),
            pytest.param({"maximum_gap_size": "5min"}, id="maximum_gap_size"),
        ],
    )
    def test_using_keywords_no_metadata(optional_arguments):
        rng = np.random.default_rng(seed=42)
        length = 100
        dates = pd.date_range("2024-01-01", periods=1000, freq="1min")[rng.integers(low=0, high=1000, size=100)]
        series = pd.Series(
            rng.random(100)
            index=dates
        )

        result = main(series=series, **optional_arguments)
        assert result_is_json(result)


