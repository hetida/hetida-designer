from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType  # add your own imports here
from hetdesrun.utils import plotly_fig_to_json_dict


import pandas as pd
import numpy as np

import plotly.express as px

import plotly.io as pio

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
    **kwargs
):

    if cat_color_mapping is None:
        cat_color_mapping = {}

    use_size_vals = False
    if fixed_size is not None and size is None:
        use_size_vals = True
        size_vals = np.ones(len(dataframe)) * fixed_size
        
    fig = px.scatter_mapbox(
        dataframe,
        lat=lat_col,
        lon=lon_col,
        hover_name=hover_title_col,
        hover_data=hover_additional_description_cols,
        size=size if not use_size_vals else size_vals,
        size_max=10,
        color_discrete_map=cat_color_mapping,
        color=cat_color_col,
        zoom=zoom,
        height=height,
        **kwargs
    )
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={
        "data": DataType.DataFrame,
        "color_map": DataType.Any,
        "cat_color_col": DataType.String,
    },
    outputs={"map_plot": DataType.PlotlyJson},
    is_pure_plot_component=True,
)
def main(*, data, color_map, cat_color_col):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {
        "map_plot": plotly_fig_to_json_dict(
            get_plotly_osm_scatter_map_figure(
                data,
                hover_title_col="name",
                hover_additional_description_cols=["description"],
                fixed_size=2,
                size_max=5,
                cat_color_col=cat_color_col,
                cat_color_mapping=color_map,
            )
        )
    }
