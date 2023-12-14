"""Documentation for component "Time Series and Value Intervals"

# Time Series and Value Intervals

## Description
Plots the `series` and each value interval in `value_interval_dict`.

## Inputs
- **series** (Pandas Series):
    Series to be visualized. Expects dtype to be float or int.

- **value_interval_dict** (dict):
    List of dictionaries containing the value intervals to be visualized. For each interval,
    distinct line and fill colors can be entered. Supported dict properties:
    - **min_value**: Integer
    - **max_value**: Integer
    - **min_value_inclusive**: Boolean
    - **max_value_inclusive**: Boolean
    - **line_color**: String, see Details for further specifications
    - **line_color**: String, see Details for further specifications
    - **display_name**: String

- **line_color** (String):
    RGB color for the margins of the value intervals. Will be applied for each interval without
    individual "line_color" set in `value_interval_dict`.

- **fill_color** (String):
    RGBA color for the area of the value intervals. Will be applied for each interval without
    individual "fill_color" set in `value_interval_dict`. The use of either RGBA or HSLA colors
    with a low opacity, e.g. a value of 0.15 for the Alpha Channel, is strongly recommended,
    to allow visibility of the data points inside the value intervals.

## Outputs
- **series_with_intervals** (Plotly Json): The generated Plotly Json. This is used by the hetida
designer frontend for plotting the results.

## Details

- Plots the data points of the `series` as line chart and the value intervals as rectangles reaching
from the first to the last data point. Each
value interval is labeled with its name.

- Accepted color inputs are:
    - A hex string (e.g. '#ff0000')
    - An rgb/rgba string (e.g. 'rgb(255,0,0)')
    - An hsl/hsla string (e.g. 'hsl(0,100%,50%,15%)')
    - A named CSS color (e.g. 'indigo')
For fill colors, the use of either RGBA or HSLA colors with a low opacity, e.g. a value of
0.15 for the Alpha Channel, is strongly recommended, to allow visibility of the data points inside
the value intervals.

- Raises `ComponentInputValidationException`:


## Examples

Example json input for a call of this component is:
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
from pydantic import BaseModel, ColorError, ValidationError, color, root_validator

from hetdesrun.runtime.exceptions import ComponentInputValidationException
from hetdesrun.utils import plotly_fig_to_json_dict


class ValueInterval(BaseModel):
    min_value: float
    min_value_inclusive: bool = True
    max_value: float
    max_value_inclusive: bool = True
    fill_color: str | None
    line_color: str | None
    display_name: str | None

    @root_validator()
    def verify_value_ranges(cls, values: dict) -> dict:
        try:
            min_value = values["min_value"]
            min_value_inclusive = values["min_value_inclusive"]
            max_value = values["max_value"]
            max_value_inclusive = values["max_value_inclusive"]
            fill_color_str = values.get("fill_color")
            if fill_color_str is not None:
                fill_color = color.Color(fill_color_str).as_rgb()
            line_color_str = values.get("line_color")
            if line_color_str is not None:
                line_color = color.Color(line_color_str).as_rgb()
            display_name = values.get("display_name")

        except (KeyError, ColorError) as error:
            raise ValueError("") from error
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


pio.templates.default = None

logger = logging.getLogger(__name__)


def plot_series_and_ranges(
    series: pd.Series,
    interval_dict: dict[str, ValueInterval],
    line_color: str,
    fill_color: str,
) -> go.Figure:
    series_to_plot = series.sort_index()
    fig = go.Figure(
        [go.Scatter(x=series_to_plot.index, y=series_to_plot, mode="lines+markers")]
    )

    time_delta = series_to_plot.index.max() - series_to_plot.index.min()
    num_intervals = len(interval_dict)

    for interval_key in interval_dict:
        fig.add_shape(
            type="rect",
            x0=series_to_plot.index.min(),
            y0=interval_dict[interval_key].min_value,
            x1=series_to_plot.index.max(),
            y1=interval_dict[interval_key].max_value,
            line={
                "color": interval_dict[interval_key].line_color
                or interval_dict[interval_key].fill_color
                or line_color,
                "width": 1,
            },
            fillcolor=interval_dict[interval_key].fill_color or fill_color,
        )

    int_i = 0

    for interval_key in interval_dict:
        x = series_to_plot.index.min() + (int_i + 1) * time_delta / (num_intervals * 12)

        fig.add_shape(
            type="line",
            x0=x,
            y0=interval_dict[interval_key].min_value,
            x1=x,
            y1=interval_dict[interval_key].max_value,
            line={
                "color": interval_dict[interval_key].line_color
                or interval_dict[interval_key].fill_color
                or line_color,
                "width": 2,
            },
            label={
                "text": interval_dict[interval_key].display_name or interval_key,
                "textangle": -90,
                "font": {"size": 10},
            },
        )
        int_i = int_i + 1

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
    "name": "Time Series and Value Intervals",
    "category": "Visualization",
    "description": "Plots the series and each value interval in value_interval_dict.",
    "version_tag": "0.1.4",
    "id": "9b4ca94e-0e20-4341-bb23-abe73d33c7ab",
    "revision_group_id": "b2c8fc6a-c550-4b4c-94f1-7cec0d87a081",
    "state": "RELEASED",
    "released_timestamp": "2023-11-08T15:09:29.370028+00:00",
}


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
            "To determine whether time series entries are in a value interval,"
            f" their dtype must be float or int, while it is {series.dtype}",
            error_code=422,
            invalid_component_inputs=["series"],
        )

    series_no_nan = series.dropna()

    if series_no_nan.empty is True:
        raise ComponentInputValidationException(
            "To determine whether time series entries are in a value interval,"
            "the input series must not be empty.",
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
    try:
        line_color_rgb = color.Color(line_color).as_rgb()
    except ColorError as error:
        raise ComponentInputValidationException(  # noqa: B904
            "There was an input validation error for the line_color:\n" + str(error),
            error_code=422,
            invalid_component_inputs=["line_color"],
        )
    try:
        fill_color_rgb = color.Color(fill_color).as_rgb()
    except ColorError as error:
        raise ComponentInputValidationException(  # noqa: B904
            "There was an input validation error for the fill_color:\n" + str(error),
            error_code=422,
            invalid_component_inputs=["fill_color"],
        )

    return {
        "series_with_intervals": plotly_fig_to_json_dict(
            plot_series_and_ranges(
                series_no_nan, value_intervals, line_color_rgb, fill_color_rgb
            )
        )
    }


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "series",
            "adapter_id": "direct_provisioning",
            "use_default_value": False,
            "filters": {
                "value": (
                    "{\n"
                    '    "2020-01-01T01:15:27.000Z": 42.0,\n'
                    '    "2020-01-01T16:20:00.000Z": 16.1,\n'
                    '    "2020-01-02T08:20:00.000Z": 27.0,\n'
                    '    "2020-01-02T16:20:00.000Z": 2.6,\n'
                    '    "2020-01-03T08:20:04.000Z": 25.9\n'
                    "}"
                )
            },
        },
        {
            "workflow_input_name": "value_interval_dict",
            "adapter_id": "direct_provisioning",
            "use_default_value": False,
            "filters": {
                "value": (
                    "{\n"
                    '    "[10,20]": {\n'
                    '        "min_value": 10.0,\n'
                    '        "max_value": 20.0,\n'
                    '        "min_value_inclusive": true,\n'
                    '        "max_value_inclusive": true,\n'
                    '        "display_name": "Intv. 1"\n'
                    "    },\n"
                    '    "(20,30)": {\n'
                    '        "min_value": 20.0,\n'
                    '        "max_value": 30.0,\n'
                    '        "min_value_inclusive": false,\n'
                    '        "max_value_inclusive": false,\n'
                    '        "line_color": "rgb(40,20,250)",\n'
                    '        "fill_color": "rgba(40,20,250,0.15)"\n'
                    "    }\n"
                    "}"
                )
            },
        },
    ],
}
