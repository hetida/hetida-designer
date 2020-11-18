from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType  # add your own imports here


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"data_1": DataType.Any, "data_2": DataType.Any},
    outputs={"data_1_restricted": DataType.Any, "data_2_restricted": DataType.Any},
)
def main(*, data_1, data_2):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    common_index = data_1.index.intersection(data_2.index)

    return {
        "data_1_restricted": data_1.loc[common_index],
        "data_2_restricted": data_2.loc[common_index],
    }
