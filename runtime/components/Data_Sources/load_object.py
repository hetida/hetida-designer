from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType  # add your own imports here
import hetdesrun.serialization

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"name": DataType.String, "tag": DataType.String},
    outputs={"obj": DataType.Any},
)
def main(*, name, tag):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {"obj": hetdesrun.serialization.load_obj(name, tag)}
