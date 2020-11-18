from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import math

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(inputs={}, outputs={"e": DataType.Float})
def main():
    """entrypoint function for this component

    Usage example:
    >>> main()
    {'e': 2.718281828459045}
    """
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {"e": math.e}
