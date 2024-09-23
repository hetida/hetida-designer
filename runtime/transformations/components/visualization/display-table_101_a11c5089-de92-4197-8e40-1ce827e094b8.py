"""Documentation for Display Table

# Display Table

## Description
Display a DataFrame as table.

## Inputs
* **data** (Pandas DataFrame): The data to be displayed.

## Outputs
* **table** (Plotly Json): The generated Plotly Json. This is used by the hetida
  designer frontend for plotting the results.
* **auto_col_width** (bool) (Default: true): Whether column width should be computed
  from content automatically.

## Details
The component generates a simple table of the provided data using Plotly.

## Examples
The json input of a typical call of this component is
```
{
        "data": {
        "col_1": ["a", "a", "a", "b", "c", "d", "b"],
        "col_2": [2, 3, 2, 4, 4, 4, 4]
    }
}
```
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from pandas.api.types import is_datetime64_any_dtype

from hdutils import plotly_fig_to_json_dict

pio.templates.default = None


def auto_col_with(series: pd.Series):
    """Try to guess a good column width for the table visualization

    When rendered, plotly tables allow to rearrange columns interactively
    but unfortunately not to resize column width.

    This can lead to unreadable values or column names with no mean
    to make it readable.

    This function tries to guess a good column width based
    on column dtype and the column name (which is used as table header)
    in order to make

    """
    dtype_col_width = 0
    if series.dtype == float:  # noqa: SIM114
        dtype_col_width = 16
    elif series.dtype == int:
        dtype_col_width = 16
    elif series.dtype == bool:
        dtype_col_width = 6
    elif pd.api.types.is_string_dtype(series):
        dtype_col_width = max([min([max(series.str.len()), 200]), 12])
        # maximal len of strings in column but:
        # at least 12
        # at most 200
    elif is_datetime64_any_dtype(series):
        dtype_col_width = 32  # microsends isoformat
    elif series.dtype == object:
        dtype_col_width = 32
    else:
        dtype_col_width = 50
    return max([dtype_col_width, len(series.name) if series.name is not None else 5])


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "data": {"data_type": "DATAFRAME"},
        "auto_col_width": {"data_type": "BOOLEAN", "default_value": True},
    },
    "outputs": {
        "table": {"data_type": "PLOTLYJSON"},
    },
    "name": "Display Table",
    "category": "Visualization",
    "description": "Display DataFrame as table",
    "version_tag": "1.0.1",
    "id": "a11c5089-de92-4197-8e40-1ce827e094b8",
    "revision_group_id": "e0320729-10df-8979-4444-feb6fe7adc82",
    "state": "RELEASED",
    "released_timestamp": "2024-02-27T11:51:15.287045+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, data, auto_col_width=True):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    columns = list(data.columns)
    fig = go.Figure(
        data=[
            go.Table(
                columnwidth=(
                    [auto_col_with(data[col]) for col in columns] if auto_col_width else None
                ),
                header=dict(  # noqa: C408
                    values=columns, fill_color="paleturquoise", align="left"
                ),
                cells=dict(  # noqa: C408
                    values=[data[col] for col in columns],
                    fill_color="lavender",
                    align="left",
                ),
            )
        ]
    )

    layout_opts: dict = {
        "xaxis_title": "Time",
        "yaxis_title": "Values",
        "autosize": True,
        "height": 400,
    }
    # scrollbars should be visible:
    fig.update_layout(margin=dict(l=0, r=15.0, b=15.0, t=5, pad=0))  # noqa: C408
    fig.update_layout(**layout_opts)
    fig.update_yaxes(automargin=True)
    fig.update_xaxes(automargin=True)

    return {"table": plotly_fig_to_json_dict(fig)}


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "data",
            "filters": {
                "value": '{\n    "very very very looooooong column name": {\n        "2019-08-01T15:45:36.000Z": 1,\n        "2019-08-02T11:33:41.000Z": 2\n    },\n    "column2": {\n        "2019-08-01T15:45:36.000Z": 1.3,\n        "2019-08-02T11:33:41.000Z": 2.8\n    },\n    "c": {\n        "2019-08-01T15:45:36.000Z": "0",\n        "2019-08-02T11:33:41.000Z": "The green fox jumps over some fence anr runs to the garden. What happens next?"        \n    }\n}'
            },
        },
        {
            "workflow_input_name": "auto_col_width",
            "use_default_value": True,
            "filters": {"value": "true"},
        },
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "data",
            "filters": {
                "value": '{\n    "very very very looooooong column name": {\n        "2019-08-01T15:45:36.000Z": 1,\n        "2019-08-02T11:33:41.000Z": 2\n    },\n    "column2": {\n        "2019-08-01T15:45:36.000Z": 1.3,\n        "2019-08-02T11:33:41.000Z": 2.8\n    },\n    "c": {\n        "2019-08-01T15:45:36.000Z": "0",\n        "2019-08-02T11:33:41.000Z": "The green fox jumps over some fence anr runs to the garden. What happens next?"        \n    }\n}'
            },
        },
        {
            "workflow_input_name": "auto_col_width",
            "use_default_value": True,
            "filters": {"value": "true"},
        },
    ]
}
