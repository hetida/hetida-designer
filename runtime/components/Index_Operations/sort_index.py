from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType  # add your own imports here


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(inputs={"data": DataType.Any}, outputs={"data": DataType.Any})
def main(*, data):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {"data": data.sort_index()}
