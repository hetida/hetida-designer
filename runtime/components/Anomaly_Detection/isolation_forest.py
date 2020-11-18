from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType  # add your own imports here


from sklearn.ensemble import IsolationForest
import pandas as pd


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={
        "test_data": DataType.DataFrame,
        "train_data": DataType.DataFrame,
        "n_estimators": DataType.Integer,
    },
    outputs={
        "decision_function_values": DataType.Series,
        "trained_model": DataType.Any,
    },
)
def main(*, test_data, train_data, n_estimators):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    iso_forest = IsolationForest(n_jobs=-1, n_estimators=n_estimators)
    iso_forest.fit(train_data)

    dec_vals = pd.Series(iso_forest.decision_function(test_data), index=test_data.index)

    return {"decision_function_values": dec_vals, "trained_model": iso_forest}

