from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType  # add your own imports here

import pandas as pd

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"data": DataType.Any, "trained_model": DataType.Any},
    outputs={"predictions": DataType.Any},
)
def main(*, data, trained_model):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    return {
        "predictions": pd.Series(
            trained_model.decision_function(data),
            index=data.index,
            name="decision_function_values",
        )
    }

