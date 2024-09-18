"""Documentation for Display Table

# Display Table

## Description
Display a DataFrame as table.

## Inputs
* **data** (Pandas DataFrame): The data to be displayed.

## Outputs
* **table** (Plotly Json): The generated Plotly Json. This is used by the hetida
  designer frontend for plotting the results.

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

import plotly.graph_objects as go
import plotly.io as pio

from hdutils import plotly_fig_to_json_dict

pio.templates.default = None


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "data": {"data_type": "DATAFRAME"},
    },
    "outputs": {
        "table": {"data_type": "PLOTLYJSON"},
    },
    "name": "Display Table",
    "category": "Visualization",
    "description": "Display DataFrame as table",
    "version_tag": "1.0.0",
    "id": "e0320729-10df-8979-4444-feb6fe7adc82",
    "revision_group_id": "e0320729-10df-8979-4444-feb6fe7adc82",
    "state": "DISABLED",
    "released_timestamp": "2022-02-09T17:33:30.368991+00:00",
    "disabled_timestamp": "2024-02-27T11:56:33.768617+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, data):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    columns = list(data.columns)
    fig = go.Figure(
        data=[
            go.Table(
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


TEST_WIRING_FROM_PY_FILE_IMPORT = {}
RELEASE_WIRING = {}
