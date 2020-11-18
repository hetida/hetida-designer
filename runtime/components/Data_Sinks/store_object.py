from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType  # add your own imports here
import hetdesrun.serialization

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"name": DataType.String, "obj": DataType.Any, "tag": DataType.String},
    outputs={},
)
def main(*, name, obj, tag):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    hetdesrun.serialization.dump_obj(obj, name, tag)
    return {}
