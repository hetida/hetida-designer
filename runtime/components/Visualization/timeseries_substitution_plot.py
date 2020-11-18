from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType  # add your own imports here
from hetdesrun.utils import plotly_fig_to_json_dict

import pandas as pd

from plotly.graph_objects import Figure
import plotly.express as px

import plotly.io as pio

pio.templates.default = None


def handle_substitutions(original_series, substitution_series):
    """Applies substituion series on raw values
    
    The substitution series can contain
    * replacement values (at indices occuring in original)
    * new values (values at indices not in original)
    * null values at indices in original marking values for invalidation (ignoring)
    
    Returns a tuple of pandas Series objects
        (completely_handled, replaced_values, replacements, new_values, ignored_values)    """

    new = original_series.copy()
    deleted = new.loc[substitution_series.isnull().reindex(new.index, fill_value=False)]

    kept_before_replacing = new.loc[
        substitution_series.notnull().reindex(new.index, fill_value=True)
    ]

    replaced_originals = new.loc[
        substitution_series.notnull().reindex(new.index, fill_value=False)
    ]

    replacements = substitution_series.reindex(original_series.index).dropna()

    new_values = substitution_series.loc[
        ~substitution_series.index.isin(original_series.index)
    ]

    completely_handled_series = new.copy()
    completely_handled_series = completely_handled_series.loc[
        substitution_series.notnull().reindex(
            completely_handled_series.index, fill_value=True
        )
    ]
    completely_handled_series.update(substitution_series)
    completely_handled_series = pd.concat([completely_handled_series, new_values])

    return (
        completely_handled_series.sort_index(),
        replaced_originals,
        replacements,
        new_values,
        deleted,
    )


def substituted_data_plot(
    raw_values: pd.Series,
    substitutions: pd.Series,
    message_series: pd.Series = None,
    traces_opts: dict = {},
    layout_opts: dict = {
        "xaxis_title": "Time",
        "yaxis_title": "Values",
        "autosize": True,
        "height": 200,
    },
    line_opts: dict = {},
) -> Figure:
    """Create a single time series line plot Plotly figure
    
    Returns the plotly figure object.
    """

    fig = Figure()

    s1 = raw_values.sort_index()
    s1 = s1.loc[~s1.index.duplicated(keep="first")]

    s2 = substitutions.sort_index()
    s2 = s2.loc[~s2.index.duplicated(keep="first")]

    completely_handled_series, replaced_originals, replacements, new_values, deleted = handle_substitutions(
        s1, s2
    )

    fig.add_scatter(
        x=completely_handled_series.index,
        y=completely_handled_series,
        mode="markers+lines",
        name=raw_values.name + "_substituted"
        if raw_values.name
        else "raw_values_substituted",
        line_color="blue",
        opacity=0.6,
    )  # Not what is desired - need a line

    fig.add_scatter(
        x=replaced_originals.index,
        y=replaced_originals,
        mode="markers",
        name="replaced raw values",
        line_color="orange",
        marker=dict(size=10, opacity=0.6),
    )  # Not what is desired - need a line

    fig.add_scatter(
        x=deleted.index,
        y=deleted,
        mode="markers",
        name="ignored raw values",
        line_color="red",
        marker=dict(symbol="x", size=10, opacity=0.6),
    )  # Not what is desired - need a line

    fig.add_scatter(
        x=new_values.index,
        y=new_values,
        mode="markers",
        name="added values",
        line_color="green",
        marker=dict(symbol="cross", size=10, opacity=0.6),
    )  # Not what is desired - need a line

    fig.update_layout(**layout_opts)  # see https://plotly.com/python/figure-labels/
    fig.update_traces(traces_opts)  # set line color?

    fig.update_layout(margin=dict(l=0, r=0, b=0, t=5, pad=0))

    fig.update_yaxes(automargin=True)
    fig.update_xaxes(automargin=True)
    return fig


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"raw_values": DataType.Series, "substitution_series": DataType.Series},
    outputs={"substituted_ts_plot": DataType.PlotlyJson},
)
def main(*, raw_values, substitution_series):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {
        "substituted_ts_plot": plotly_fig_to_json_dict(
            substituted_data_plot(raw_values, substitution_series)
        )
    }
