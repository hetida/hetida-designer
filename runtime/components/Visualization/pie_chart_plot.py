from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType
from hetdesrun.utils import plotly_fig_to_json_dict


import pandas as pd

from plotly.graph_objects import Figure
import plotly.express as px

import plotly.io as pio

pio.templates.default = None


def plotly_pie_chart_plot(
    dataframe: pd.DataFrame,
    values_column_name: str,
    groups_column_name: str,
    traces_opts: dict = {},
    layout_opts: dict = {"height": 300, "width": 300},
    pie_opts: dict = {},
) -> Figure:
    """Create a pie chart plot Plotly figure
    
    Expects a dataframe, a values_column_name selecting the column
    in the dataframe to sum up. Then groups_column_name selects the groups
    of values whose relative fraction of the sum should be shown in the Pie Chart.
    
    
    Returns the plotly figure object.
    """

    fig = px.pie(
        dataframe, values=values_column_name, names=groups_column_name, **pie_opts
    )

    fig.update_layout(**layout_opts)  # see https://plotly.com/python/figure-labels/
    fig.update_traces(**traces_opts)  # set line color?
    fig.update_layout(margin=dict(l=0, r=0, b=0, t=5, pad=0))

    fig.update_yaxes(automargin=True)
    fig.update_xaxes(automargin=True)

    return fig


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={
        "dataframe": DataType.DataFrame,
        "value_column": DataType.String,
        "group_column": DataType.String,
    },
    outputs={"plot": DataType.PlotlyJson},
    is_pure_plot_component=True,
)
def main(*, dataframe, value_column, group_column):
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {
        "plot": plotly_fig_to_json_dict(
            plotly_pie_chart_plot(dataframe, value_column, group_column)
        )
    }
