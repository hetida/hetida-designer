from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType
from hetdesrun.utils import plotly_fig_to_json_dict

import pandas as pd

from plotly.graph_objects import Figure
import plotly.graph_objects as go


import plotly.io as pio

pio.templates.default = None

sns_colorscale = [
    [0.0, "#3f7f93"],  # cmap = sns.diverging_palette(220, 10, as_cmap = True)
    [0.071, "#5890a1"],
    [0.143, "#72a1b0"],
    [0.214, "#8cb3bf"],
    [0.286, "#a7c5cf"],
    [0.357, "#c0d6dd"],
    [0.429, "#dae8ec"],
    [0.5, "#f2f2f2"],
    [0.571, "#f7d7d9"],
    [0.643, "#f2bcc0"],
    [0.714, "#eda3a9"],
    [0.786, "#e8888f"],
    [0.857, "#e36e76"],
    [0.929, "#de535e"],
    [1.0, "#d93a46"],
]


def correlation_heatmap(dataframe):
    corr_df = dataframe.corr()

    heat = go.Heatmap(
        z=corr_df.values,
        x=corr_df.columns,
        y=corr_df.columns,
        xgap=1,
        ygap=1,
        colorscale=sns_colorscale,
        colorbar_thickness=20,
        colorbar_ticklen=3,
        hovertext=corr_df.astype(str),
        hoverinfo="text",
    )

    title = "Correlation Matrix Heatmap"

    layout = go.Layout(
        # title_text=title,
        # title_x=0.5,
        width=440,
        height=400,
        xaxis_showgrid=False,
        yaxis_showgrid=False,
        yaxis_autorange="reversed",
    )

    fig = go.Figure(data=[heat], layout=layout)

    fig.update_layout(margin=dict(l=0, r=0, b=0, t=5, pad=0))
    fig.update_yaxes(automargin=True)
    fig.update_xaxes(automargin=True)

    return fig


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"dataframe": DataType.DataFrame},
    outputs={"plot": DataType.PlotlyJson},
    is_pure_plot_component=True,
)
def main(*, dataframe):
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {"plot": plotly_fig_to_json_dict(correlation_heatmap(dataframe))}
