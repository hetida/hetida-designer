from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={
        "column_name": DataType.String,
        "dataframe_left": DataType.DataFrame,
        "dataframe_right": DataType.DataFrame,
        "how": DataType.String,
    },
    outputs={"merged_dataframe": DataType.DataFrame},
)
def main(*, column_name, dataframe_left, dataframe_right, how="inner"):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    merged_dataframe = dataframe_left.merge(
        dataframe_right, left_on=column_name, right_on=column_name, how=how
    )

    return {"merged_dataframe": merged_dataframe}

