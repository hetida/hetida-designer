from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(inputs={"input": DataType.DataFrame}, outputs={"output": DataType.DataFrame})
def main(*, input):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    return {"output": input}
