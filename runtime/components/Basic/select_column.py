from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType  # add your own imports here


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"dataframe": DataType.DataFrame, "column": DataType.String},
    outputs={"column_series": DataType.Series},
)
def main(*, dataframe, column):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    return {"column_series": dataframe[column]}
