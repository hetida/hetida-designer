from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import math

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(inputs={}, outputs={"pi": DataType.Float})
def main():
    """entrypoint function for this component

    Usage example:
    >>> main()
    {'pi': 3.141592653589793}
    """
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {"pi": math.pi}
