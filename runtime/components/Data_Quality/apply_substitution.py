from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType  # add your own imports here
from hetdesrun.utils import plotly_fig_to_json_dict

import pandas as pd


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

    s1 = raw_values.sort_index()
    s1 = s1.loc[~s1.index.duplicated(keep="first")]

    s2 = substitution_series.sort_index()
    s2 = s2.loc[~s2.index.duplicated(keep="first")]
    return {"substituted_ts": handle_substitutions(s1, s2)[0]}
