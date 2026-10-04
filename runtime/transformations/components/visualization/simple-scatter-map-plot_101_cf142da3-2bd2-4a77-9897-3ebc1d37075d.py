"""Documentation for Simple Scatter Map Plot

# Simple Scatter Map Plot

## Description
This component marks locations on a map.

## Inputs
* **data** (Pandas DataFrame): Must have
 * "lat" and a "lon" columns containing latitude and longitude coordinates
 * "name" column where the titles of the hovering rectangle are obtained from.
 * "description" column where additional information is stored that is included in the hovering rectangles.
 * A column of which the name is equal to the value provided in **cat_color_col** input. This must be a categorical column, e.g. String values like `"A", "B", ...`.
* **color_map** (Any): Must be a dictionary providing color values for the category values in `data[cat_color_col]`, e.g. `{"A": "#005099", "B": "#6633FF"}`
* **cat_color_col** (String): The name of the column containing the categories in **data**.

## Outputs
* **map_plot** (Plotly Json): The generated Plotly Json map plot. This is used by the hetida designer frontend for plotting the results.

## Details
This is an example for a Scatter Map plot. It draws an Openstreetmap map, marking all locations in **data** with a small circle. The map is centered on the mean of the provided coordinates.

In contrast to revision 1.0.0, this revision uses Plotly's MapLibre based map plots instead of the Mapbox based ones, which are removed in Plotly 7.

## Examples
The json input of a typical call of this component is
```
{
    "cat_color_col": "Organisation",
    "color_map": {
        "Folkwang": "#005099",
        "von der Heydt": "#00925B",
        "lehmbruck": "#0076BD"
    },
    "data": {
        "lat": [
            51.442666,
            51.256625,
            51.430145
        ],
        "lon": [
            7.005126,
            7.146598,
            6.765380
        ],
        "name": [
            "Folkwang Museum Essen",
            "Von der Heydt Museum Wuppertal",
            "Lehmbruck Museum Duisburg"
        ],
        "description": [
            "",
            "",
            ""
        ],
        "Organisation": [
            "Folkwang",
            "von der Heydt",
            "lehmbruck"
        ]
    }
}
```
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.io as pio

from hdutils import plotly_fig_to_json_dict

pio.templates.default = None


def get_plotly_osm_scatter_map_figure(
    dataframe,
    lat_col="lat",
    lon_col="lon",
    hover_title_col=None,
    hover_additional_description_cols=None,
    cat_color_col=None,
    cat_color_mapping=None,
    size=None,
    fixed_size=None,
    size_max=10,
    zoom=8,
    height=400,
    **kwargs,
):
    if cat_color_mapping is None:
        cat_color_mapping = {}

    use_size_vals = False
    if fixed_size is not None and size is None:
        use_size_vals = True
        size_vals = np.ones(len(dataframe)) * fixed_size

    # Plotly >= 7 does not center the map on the data anymore if a zoom is given
    center = {"lat": dataframe[lat_col].mean(), "lon": dataframe[lon_col].mean()}

    fig = px.scatter_map(
        dataframe,
        lat=lat_col,
        lon=lon_col,
        hover_name=hover_title_col,
        hover_data=hover_additional_description_cols,
        size=size if not use_size_vals else size_vals,
        size_max=size_max,
        color_discrete_map=cat_color_mapping,
        color=cat_color_col,
        center=center,
        zoom=zoom,
        height=height,
        map_style="open-street-map",
        **kwargs,
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "data": {"data_type": "DATAFRAME"},
        "color_map": {"data_type": "ANY"},
        "cat_color_col": {"data_type": "STRING"},
    },
    "outputs": {
        "map_plot": {"data_type": "PLOTLYJSON"},
    },
    "name": "Simple Scatter Map Plot",
    "category": "Visualization",
    "description": "Mark locations on a map",
    "version_tag": "1.0.1",
    "id": "cf142da3-2bd2-4a77-9897-3ebc1d37075d",
    "revision_group_id": "dc909fa2-93fa-3205-e31d-b05f944cbd29",
    "state": "RELEASED",
    "released_timestamp": "2026-09-29T14:37:33.825173+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, data, color_map, cat_color_col):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {
        "map_plot": plotly_fig_to_json_dict(
            get_plotly_osm_scatter_map_figure(
                data,
                hover_title_col="name",
                hover_additional_description_cols=["description"],
                fixed_size=2,
                cat_color_col=cat_color_col,
                cat_color_mapping=color_map,
            )
        )
    }


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "data",
            "filters": {
                "value": '{\n    "lat": [51.442666, 51.256625, 51.430145],\n    "lon": [7.005126, 7.146598, 6.765380],\n    "name": ["Folkwang Museum Essen", "Von der Heydt Museum Wuppertal", "Lehmbruck Museum Duisburg"],\n    "description": ["", "", ""],\n    "Organisation": ["Folkwang", "von der Heydt", "lehmbruck"]\n}'
            },
        },
        {
            "workflow_input_name": "color_map",
            "filters": {
                "value": '{\n    "Folkwang": "#005099",\n    "von der Heydt": "#00925B",\n    "lehmbruck": "#0076BD"\n}'
            },
        },
        {"workflow_input_name": "cat_color_col", "filters": {"value": "Organisation"}},
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "data",
            "filters": {
                "value": '{\n    "lat": [51.442666, 51.256625, 51.430145],\n    "lon": [7.005126, 7.146598, 6.765380],\n    "name": ["Folkwang Museum Essen", "Von der Heydt Museum Wuppertal", "Lehmbruck Museum Duisburg"],\n    "description": ["", "", ""],\n    "Organisation": ["Folkwang", "von der Heydt", "lehmbruck"]\n}'
            },
        },
        {
            "workflow_input_name": "color_map",
            "filters": {
                "value": '{\n    "Folkwang": "#005099",\n    "von der Heydt": "#00925B",\n    "lehmbruck": "#0076BD"\n}'
            },
        },
        {"workflow_input_name": "cat_color_col", "filters": {"value": "Organisation"}},
    ]
}


def test_map_plot_is_centered_on_locations():
    data = pd.DataFrame(
        {
            "lat": [51.0, 52.0],
            "lon": [7.0, 8.0],
            "name": ["A1", "B1"],
            "description": ["", ""],
            "category": ["A", "B"],
        }
    )

    map_plot = main(
        data=data, color_map={"A": "#005099", "B": "#00925B"}, cat_color_col="category"
    )["map_plot"]

    assert {trace["type"] for trace in map_plot["data"]} == {"scattermap"}  # noqa: S101
    assert map_plot["layout"]["map"]["style"] == "open-street-map"  # noqa: S101
    assert map_plot["layout"]["map"]["center"] == {"lat": 51.5, "lon": 7.5}  # noqa: S101
