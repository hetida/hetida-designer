"""Documentation for Single Timeseries Plot

# Single Timeseries Plot

## Description
Plotting a single timeseries with Plotly.

## Inputs
* **series** (Pandas Series): Entries must be numeric and Index should be a DateTime Index.

## Outputs
* **plot** (Plotly Json): The generated Plotly Json. This is used by the hetida designer frontend for plotting the results.

## Details
The component plots the incoming **series** using Plotly.

## Examples
The json input of a typical call of this component is
```
{
    "series": {
        "__hd_wrapped_data_object__": "SERIES",
        "__metadata__": {
            "dataset_metadata": {
                "ref_interval_start_timestamp": "2019-11-30T09:00:00.000Z",
                "ref_interval_end_timestamp": "2019-11-30T13:00:00.000Z",
                "ref_interval_type": "closed",
            },
            "single_metric_metadata": {
                "structured_metadata": {
                    "metric": {
                        "name": "Aktueller Niederschlag",
                        "display_name": null,
                        "short_display_name": null,
                        "description": "Aktuelle mittlere Niederschlagsrate.",
                        "unit": "mm/h",
                        "measurement": null,
                        "value_data_type": null,
                        "external_id": "precipitation_in_mmh",
                        "signal_id": "ff05d22b-1968-47d2-9683-e7598723cd56"
                    },
                    "comments": [],
                    "inherited": {},
                    }
                }
            }
        },
        "__data__": {
            "2019-11-30T09:00:00.000Z": 0,
            "2019-11-30T10:00:00.000Z": 1,
            "2019-11-30T11:00:00.000Z": 0,

        }
    },
    "__data_parsing_options__": {
        "orient": "split"
    }
}
```
"""

from hdutils import plotly_fig_to_json_dict

from hdhelpers.metadata import get_series_name, get_series_unit, get_queried_interval
from hdhelpers.helpers import modify_timezone
import pandas as pd
import plotly.graph_objects as go
from plotly.graph_objects import Figure
import plotly.express as px
import plotly.io as pio

pio.templates.default = None


def single_plotly_timeseries_plot(
    series: pd.Series,
    traces_opts: dict = {"line_color": "#1199bb"},
) -> Figure:
    """Create a single time series line plot Plotly figure

    Returns the plotly figure object.
    """

    series_with_tz = modify_timezone(series)

    df = pd.DataFrame(
        {"value": series_with_tz, "timestamp": series_with_tz.index},
        index=series_with_tz.index,
    ).sort_index()

    fig = go.Figure([go.Scatter(x=df.index, y=df["value"], mode="lines")])

    xmin, xmax = get_queried_interval(series)

    y_title = "Values"
    if get_series_name(series_with_tz) is not None:
        y_title = get_series_name(series_with_tz)
    if get_series_unit(series_with_tz) is not None:
        y_title = y_title + f" [{get_series_unit(series_with_tz)}]"

    layout_opts: dict = {
        "autosize": True,
        "height": 200,
        "yaxis_title": y_title,
    }

    fig.update_layout(**layout_opts)  # see https://plotly.com/python/figure-labels/
    fig.update_traces(traces_opts)  # set line color?

    fig.update_layout(margin=dict(l=0, r=0, b=0, t=5, pad=0))

    fig.update_yaxes(automargin=True)

    fig.update_xaxes(automargin=True, range=[xmin, xmax])

    return fig


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "series": {"data_type": "SERIES"},
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
    "released_timestamp": "2026-05-21T11:22:26.487242+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, series):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {"plot": plotly_fig_to_json_dict(single_plotly_timeseries_plot(series))}


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
