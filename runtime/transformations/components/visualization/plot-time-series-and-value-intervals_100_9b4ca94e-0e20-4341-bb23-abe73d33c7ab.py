"""Documentation for component "Plot Time Series and Value Intervals"

# Plot Time Series and Value Intervals

## Description
Plots the `series` and each value interval in `value_interval_dict`.

## Inputs
- **series** (Pandas Series):
    Series to be visualized. Expects dtype to be float or int.

- **value_interval_dict** (Any):
    A dictionary of key-value pairs, where each key is the name for a value interval and each value
    is a dictionary containing information about the value interval to be visualized. An example of
    a JSON input for a value interval dictionary is:
    ```
    {
        "[10,20]": {
            "min_value": 10.0,
            "max_value": 20.0,
            "min_value_inclusive": true,
            "max_value_inclusive": true,
            "display_name": "Intv. 1",
            "line_color": "rgb(40,20,250)",
            "fill_color": "rgba(40,20,250,0.15)"
        }
    }
    ```
    The minimum and maximum values set the boundary values of the respective value interval. The
    corresponding `_inclusive` boolean sets whether the respective boundary is inclusive or not.
    The two values shown in the example represent the default values. For each interval, different
    line and fill colors can be specified with the corresponding color properties. All
    specifications except `min_value` and `max_value` are optional. If no line color (or fill color)
    string is specified as a property, the line color (or fill color) is set to the value of the
    input `line_color` (or `fill_color`). If no display name is specified, the key of the value
    interval dictionary is used instead.

- **line_color** (String):
    Color for the margins of the value intervals. Will be applied for each interval without
    individual "line_color" set in `value_interval_dict`.

- **fill_color** (String):
    Color for the area of the value intervals. Will be applied for each interval without
    individual "fill_color" set in `value_interval_dict`. The use of colors
    with a low opacity, i.e. value for the Alpha Channel, is strongly recommended,
    to allow visibility of the data points inside the value intervals (e.g. 'rgba(255,0,0,0.15)',
    'hsl(0,100%,50%,15%)').

## Outputs
- **series_with_intervals** (Plotly Json): The generated Plotly Json. This is used by the hetida
designer frontend for plotting the results.

## Details

Plots the data points of the `series` as line chart and the value intervals as rectangles reaching
from the first to the last data point. Each value interval is labeled with its `display_name` or
the corresponding key from `value_interval_dict` if no `display_name` is set.

- Color inputs are passed to plotly. Please refer to plotly documentation (e.g.
https://plotly.com/python-api-reference/generated/plotly.graph_objects.layout.html) for accepted
input strings.

- For fill colors, the use of colors with a low opacity, i.e. a low value for the Alpha Channel, is
strongly recommended. This measure enables visibility of the data points within the value intervals
(e.g. 'rgba(255,0,0,0.15)', 'hsl(0,100%,50%,15%)').

- Raises `ComponentInputValidationException`:
    - If `series` has no entries or its dtype is neither int nor float.
    - If any value interval in `value_interval_dict` contains invalid values.

## Examples

An example JSON input for a call of this component is:
```
{
    "series": {
        "2020-01-01T01:15:27.000Z": 42.0,
        "2020-01-01T16:20:00.000Z": 16.1,
        "2020-01-02T08:20:00.000Z": 27.0,
        "2020-01-02T16:20:00.000Z": 2.6,
        "2020-01-03T08:20:04.000Z": 25.9
    },
    "value_interval_dict": {
        "[10,20]": {
            "min_value": 10.0,
            "max_value": 20.0,
            "min_value_inclusive": true,
            "max_value_inclusive": true,
            "display_name": "Intv. 1"
        },
        "(20,30)": {
            "min_value": 20.0,
            "max_value": 30.0,
            "min_value_inclusive": false,
            "max_value_inclusive": false,
            "line_color": "rgb(40,20,250)",
            "fill_color": "rgba(40,20,250,0.15)"
        }
    },
    "line_color": "rgb(40, 20, 250)",
    "fill_color": "rgba(40, 20, 250, 0.15)"
}
```

"""

import logging

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from pydantic import BaseModel, ValidationError, root_validator

from hdutils import ComponentInputValidationException, plotly_fig_to_json_dict

pio.templates.default = None

logger = logging.getLogger(__name__)


class ValueInterval(BaseModel):
    min_value: float
    min_value_inclusive: bool = True
    max_value: float
    max_value_inclusive: bool = True
    fill_color: str | None
    line_color: str | None
    display_name: str | None

    @root_validator(skip_on_failure=True)
    def verify_value_ranges(cls, values: dict) -> dict:
        min_value = values["min_value"]
        min_value_inclusive = values["min_value_inclusive"]
        max_value = values["max_value"]
        max_value_inclusive = values["max_value_inclusive"]
        if max_value < min_value:
            raise ValueError(
                "To be valid, a value interval must be non-empty, i.e. min_value may not "
                "be bigger than max_value."
            )

        if (min_value_inclusive is False or max_value_inclusive is False) and not (
            min_value < max_value
        ):
            raise ValueError(
                "To be valid, a value interval must be non-empty, i.e min_value must "
                "be smaller than max_value."
            )
        return values


def plot_series_and_ranges(
    series: pd.Series,
    interval_dict: dict[str, ValueInterval],
    line_color: str,
    fill_color: str,
) -> go.Figure:
    series_to_plot = series.sort_index()
    fig = go.Figure([go.Scatter(x=series_to_plot.index, y=series_to_plot, mode="lines+markers")])

    time_delta = series_to_plot.index.max() - series_to_plot.index.min()
    num_intervals = len(interval_dict)

    # adds a colored rectangle for each value interval
    for _, interval_value in interval_dict.items():
        fig.add_shape(
            type="rect",
            x0=series_to_plot.index.min(),
            y0=interval_value.min_value,
            x1=series_to_plot.index.max(),
            y1=interval_value.max_value,
            line={
                "color": interval_value.line_color or interval_value.fill_color or line_color,
                "width": 1,
            },
            fillcolor=interval_value.fill_color or fill_color,
        )

    # adds a colored vertical line and a label for each value interval
    for interval_index, (interval_key, interval_value) in enumerate(interval_dict.items()):
        x = series_to_plot.index.min() + (interval_index + 1) * time_delta / (num_intervals * 12)

        fig.add_shape(
            type="line",
            x0=x,
            y0=interval_value.min_value,
            x1=x,
            y1=interval_value.max_value,
            line={
                "color": interval_value.line_color or interval_value.fill_color or line_color,
                "width": 2,
            },
            label={
                "text": interval_value.display_name or interval_key,
                "textangle": -90,
                "font": {"size": 10},
            },
        )

    layout_opts: dict = {
        "xaxis_title": "Time",
        "yaxis_title": "Values",
        "autosize": True,
        "height": 200,
    }
    if series.name is not None:
        layout_opts["yaxis_title"] = series.name
    fig.update_layout(**layout_opts)  # see https://plotly.com/python/figure-labels/

    fig.update_layout(margin={"l": 0, "r": 0, "b": 0, "t": 5, "pad": 0})

    fig.update_yaxes(automargin=True)
    fig.update_xaxes(automargin=True)

    return fig


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "series": {"data_type": "SERIES"},
        "value_interval_dict": {"data_type": "ANY"},
        "line_color": {"data_type": "STRING", "default_value": "rgb(40, 251, 0)"},
        "fill_color": {
            "data_type": "STRING",
            "default_value": "rgba(40, 251, 0, 0.15)",
        },
    },
    "outputs": {
        "series_with_intervals": {"data_type": "PLOTLYJSON"},
    },
    "name": "Plot Time Series and Value Intervals",
    "category": "Visualization",
    "description": "Plots the series and each value interval in value_interval_dict.",
    "version_tag": "1.0.0",
    "id": "9b4ca94e-0e20-4341-bb23-abe73d33c7ab",
    "revision_group_id": "b2c8fc6a-c550-4b4c-94f1-7cec0d87a081",
    "state": "RELEASED",
    "released_timestamp": "2023-11-08T15:09:29.370028+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(
    *,
    series,
    value_interval_dict,
    line_color="rgb(40, 251, 0)",
    fill_color="rgba(40, 251, 0, 0.15)",
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    if series.dtype not in [int, float]:
        raise ComponentInputValidationException(
            "To display the time series entries,"
            f" their dtype must be float or int, while it is {series.dtype}",
            error_code=422,
            invalid_component_inputs=["series"],
        )

    error_dict = {}

    value_intervals: dict[str, ValueInterval] = {}

    for interval_name, value_interval in value_interval_dict.items():
        try:
            value_intervals[interval_name] = ValueInterval(**value_interval)
        except (ValueError, ValidationError) as error:
            error_dict[interval_name] = str(error)

    if len(error_dict) != 0:
        raise ComponentInputValidationException(
            "There were input validation errors for the value_interval_dict:\n"
            + "\n".join(
                interval_name + ": " + error_string
                for interval_name, error_string in error_dict.items()
            ),
            error_code=422,
            invalid_component_inputs=["value_interval_dict"],
        )

    return {
        "series_with_intervals": plotly_fig_to_json_dict(
            plot_series_and_ranges(series, value_intervals, line_color, fill_color)
        )
    }


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "series",
            "filters": {
                "value": '{\n    "2020-01-01T01:15:27.000Z": 42.0,\n    "2020-01-01T16:20:00.000Z": 16.1,\n    "2020-01-02T08:20:00.000Z": 27.0,\n    "2020-01-02T16:20:00.000Z": 2.6,\n    "2020-01-03T08:20:04.000Z": 25.9\n}'  # noqa: E501
            },
        },
        {
            "workflow_input_name": "value_interval_dict",
            "filters": {
                "value": '{\n    "[10,20]": {\n        "min_value": 10.0,\n        "max_value": 20.0,\n        "min_value_inclusive": true,\n        "max_value_inclusive": true,\n        "display_name": "Intv. 1"\n    },\n    "(20,30)": {\n        "min_value": 20.0,\n        "max_value": 30.0,\n        "min_value_inclusive": false,\n        "max_value_inclusive": false,\n        "line_color": "rgb(40,20,250)",\n        "fill_color": "rgba(40,20,250,0.15)"\n    }\n}'  # noqa: E501
            },
        },
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "series",
            "filters": {
                "value": '{\n    "2020-01-01T01:15:27.000Z": 42.0,\n    "2020-01-01T16:20:00.000Z": 16.1,\n    "2020-01-02T08:20:00.000Z": 27.0,\n    "2020-01-02T16:20:00.000Z": 2.6,\n    "2020-01-03T08:20:04.000Z": 25.9\n}'  # noqa: E501
            },
        },
        {
            "workflow_input_name": "value_interval_dict",
            "filters": {
                "value": '{\n    "[10,20]": {\n        "min_value": 10.0,\n        "max_value": 20.0,\n        "min_value_inclusive": true,\n        "max_value_inclusive": true,\n        "display_name": "Intv. 1"\n    },\n    "(20,30)": {\n        "min_value": 20.0,\n        "max_value": 30.0,\n        "min_value_inclusive": false,\n        "max_value_inclusive": false,\n        "line_color": "rgb(40,20,250)",\n        "fill_color": "rgba(40,20,250,0.15)"\n    }\n}'  # noqa: E501
            },
        },
    ]
}
