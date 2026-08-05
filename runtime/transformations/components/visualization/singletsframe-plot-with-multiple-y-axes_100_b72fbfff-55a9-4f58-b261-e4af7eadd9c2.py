"""Documentation for SingleTSFrame Plot with multiple Y Axes

# SingleTSFrame Plot with multiple Y Axes

## Description
Plotting a singletsframe with individually movable and scalable Y axes per value dimension.

## Inputs
* **singletsframe** (SingleTSFrame): A single, possibly multi-dimensional timeseries. At least one value dimension must be numeric.

## Outputs
* **plot** (Plotly Json): The generated Plotly Json. This is used by the hetida designer frontend for plotting the results.

## Details
The component plots the incoming **singletsframe** using Plotly such that each numeric value dimension (i.e. each numeric column besides "timestamp") gets its own y axis. Each y axis can be individually moved and scaled.

This is the SingleTSFrame counterpart of "MultiTsFrame Plot with multiple Y Axes": since a SingleTSFrame holds exactly one metric, the traces are its value dimensions instead of its metrics.

Non-numeric value dimensions (e.g. a string-valued quality flag) are skipped. If the [metadata conventions](https://hetida.github.io/hetida-designer/user_guide/attached_metadata/) are followed, the display name and unit of each value dimension are taken from the metadata for the trace names.

Raises an InsufficientPlottingData exception if no numeric value dimension is present.
"""

import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objs
import plotly.io as pio
from pandas.api.types import is_bool_dtype, is_numeric_dtype

from hdutils import InsufficientPlottingData, plotly_fig_to_json_dict

pio.templates.default = None


def compute_plot_positions(num_y_axes, horizontal_relative_space_per_y_axis=0.06, side="left"):
    """
    returns tuple plot_area_x_ratio, y_positions

    First assumes that a y axis horizontally fits into 5% of the total figure width
    and tries to reserve enough horizontal space to match that exactly up to a limit
    of reserving half the available width.

    If that is not possible it reserves exactly 0.5 times the total width and
    uniformly arranges the y axis positions (now having less than 5% horizontal space
    and therefore maybe overlapping)
    """

    hor_ratio = horizontal_relative_space_per_y_axis

    if num_y_axes * hor_ratio < 0.5:
        positions = [1 - x * hor_ratio - hor_ratio * (side == "right") for x in range(num_y_axes)]
        plot_area_x_ratio = 1 - num_y_axes * hor_ratio
    else:
        plot_area_x_ratio = 0.5
        positions = [1 - x * 0.5 / num_y_axes for x in range(num_y_axes)]
    return plot_area_x_ratio, positions


def trace_names_from_metadata(singletsframe, value_columns):
    """Trace name per value dimension, using metadata if it follows the conventions

    Falls back to the plain column name if no metadata is available or if the metadata
    helpers are not importable.
    """
    names = dict.fromkeys(value_columns)
    units = dict.fromkeys(value_columns)

    try:
        from hetdesrun.helpers.metadata import (  # noqa: PLC0415
            get_singlets_display_names,
            get_singlets_units,
        )

        names = get_singlets_display_names(singletsframe)
        units = get_singlets_units(singletsframe)
    except Exception:  # noqa: BLE001, S110
        pass

    trace_names = {}
    for column in value_columns:
        name = names[column] if names[column] is not None else str(column)
        unit = units[column]
        trace_names[column] = f"{name} [{unit}]" if unit not in (None, "") else name
    return trace_names


def singlets_frame_with_multi_yaxis(df):
    """One y_axis for each numeric value dimension of the input singletsframe"""

    value_columns = [
        column
        for column in df.columns
        if column != "timestamp" and is_numeric_dtype(df[column]) and not is_bool_dtype(df[column])
    ]

    if len(value_columns) == 0:
        raise InsufficientPlottingData(
            "The provided SingleTSFrame has no numeric value dimension to plot."
        )

    trace_names = trace_names_from_metadata(df, value_columns)

    timestamps = pd.to_datetime(df["timestamp"])

    plotly_data = []
    colors = px.colors.qualitative.Plotly

    sep_ratio, positions = compute_plot_positions(len(value_columns), side="right")

    layout_kwargs = {
        "xaxis": {"domain": [0, sep_ratio]},
        "height": 200,
    }

    for i, column in enumerate(value_columns):
        # we define our layout keys by string concatenation
        # * (i > 0) is just to get rid of the if i > 0 statement
        axis_name = "yaxis" + str(i + 1) * (i > 0)
        yaxis = "y" + str(i + 1) * (i > 0)
        plotly_data.append(
            plotly.graph_objs.Scatter(
                x=timestamps,
                y=df[column],
                name=trace_names[column],
                line={"color": colors[i % len(colors)]},
            )
        )

        layout_kwargs[axis_name] = {
            "position": positions[i],
            "side": "right",  # which side of the anchor
            "tickfont": {"color": colors[i % len(colors)], "size": 12},
            "showline": True,  # axis line
            "linecolor": colors[i % len(colors)],  # axis line color
            "showgrid": True,
        }

        plotly_data[i]["yaxis"] = yaxis
        if i > 0:
            layout_kwargs[axis_name]["overlaying"] = "y"

    fig = plotly.graph_objs.Figure(
        data=plotly_data, layout=plotly.graph_objs.Layout(**layout_kwargs)
    )
    fig.update_layout(margin={"l": 0, "r": 0, "b": 0, "t": 5, "pad": 0})

    return fig


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "singletsframe": {"data_type": "SINGLETSFRAME"},
    },
    "outputs": {
        "plot": {"data_type": "PLOTLYJSON"},
    },
    "name": "SingleTSFrame Plot with multiple Y Axes",
    "category": "Visualization",
    "description": "Plotting a singletsframe with one Y axis per value dimension",
    "version_tag": "1.0.0",
    "id": "b72fbfff-55a9-4f58-b261-e4af7eadd9c2",
    "revision_group_id": "a6a77ede-99b5-42a3-a357-be94e7f71b87",
    "state": "RELEASED",
    "released_timestamp": "2026-08-05T10:00:00+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, singletsframe):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {"plot": plotly_fig_to_json_dict(singlets_frame_with_multi_yaxis(singletsframe))}


# Testing
try:
    import pytest
except ImportError:
    pass
else:

    @pytest.fixture
    def singletsframe():
        singletsframe = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(
                    ["2019-08-01T15:42:36.000Z", "2019-08-01T15:45:36.000Z"], utc=True
                ),
                "value": [1.0, 1.2],
                "score": [0.7, 0.2],
                "state": ["ok", "suspicious"],
            }
        )
        singletsframe.attrs = {
            "dataset_metadata": {"single_metric": "abc.temp"},
            "metrics": [
                {
                    "id": "abc.temp",
                    "value_dimensions": [
                        {"column": "value", "name": "temperature", "unit": "°C"},
                    ],
                }
            ],
        }
        return singletsframe

    def test_one_trace_per_numeric_value_dimension(singletsframe):
        plot = main(singletsframe=singletsframe)["plot"]

        # "state" is not numeric and therefore skipped
        assert len(plot["data"]) == 2  # noqa: S101
        assert plot["data"][0]["name"] == "temperature [°C]"  # noqa: S101
        assert plot["data"][1]["name"] == "score"  # noqa: S101

    def test_no_metadata_falls_back_to_column_names(singletsframe):
        singletsframe.attrs = {}

        plot = main(singletsframe=singletsframe)["plot"]

        assert [trace["name"] for trace in plot["data"]] == ["value", "score"]  # noqa: S101

    def test_no_numeric_value_dimension_raises(singletsframe):
        with pytest.raises(InsufficientPlottingData):
            main(singletsframe=singletsframe[["timestamp", "state"]])


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "singletsframe",
            "filters": {
                "value": '{\n    "__hd_wrapped_data_object__": "DATAFRAME",\n    "__metadata__": {\n        "dataset_metadata": {\n            "single_metric": "abc.temp"\n        },\n        "metrics": [\n            {\n                "id": "abc.temp",\n                "value_dimensions": [\n                    {\n                        "column": "value",\n                        "name": "temperature",\n                        "unit": "\\u00b0C"\n                    }\n                ]\n            }\n        ]\n    },\n    "__data__": {\n        "timestamp": {\n            "0": "2022-07-01T13:00:00.000Z",\n            "1": "2022-07-01T14:00:00.000Z",\n            "2": "2022-07-01T15:00:00.000Z",\n            "3": "2022-07-01T16:00:00.000Z",\n            "4": "2022-07-01T17:00:00.000Z"\n        },\n        "value": {\n            "0": 21.4,\n            "1": 22.1,\n            "2": 23.7,\n            "3": 22.9,\n            "4": 21.8\n        },\n        "score": {\n            "0": 0.1,\n            "1": 0.15,\n            "2": 0.8,\n            "3": 0.4,\n            "4": 0.05\n        }\n    }\n}'
            },
        }
    ]
}
RELEASE_WIRING = {}
