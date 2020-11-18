from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType
from hetdesrun.utils import plotly_fig_to_json_dict

import plotly.graph_objects as go

import plotly.io as pio

pio.templates.default = None


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"data": DataType.DataFrame},
    outputs={"table": DataType.PlotlyJson},
    is_pure_plot_component=True,
)
def main(*, data):
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    columns = list(data.columns)
    fig = go.Figure(
        data=[
            go.Table(
                header=dict(values=columns, fill_color="paleturquoise", align="left"),
                cells=dict(
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
    fig.update_layout(margin=dict(l=0, r=15.0, b=15.0, t=5, pad=0))
    fig.update_layout(**layout_opts)
    fig.update_yaxes(automargin=True)
    fig.update_xaxes(automargin=True)

    return {"table": plotly_fig_to_json_dict(fig)}
