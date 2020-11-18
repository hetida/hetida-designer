from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(inputs={"dataframe": DataType.DataFrame}, outputs={"series": DataType.Series})
def main(*, dataframe):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    return {"series": dataframe.squeeze()}
