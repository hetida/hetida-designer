from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(inputs={"data": DataType.Series}, outputs={"sum": DataType.Float})
def main(*, data):
    """entrypoint function for this component

    Usage example:
    >>> import pandas as pd
    >>> main(
    ...     data = pd.Series(
    ...        {
    ... 	"2019-08-01T15:20:12": 0,
    ...	"2019-08-01T15:44:12": 3,
    ...	"2019-08-03T16:20:15": None
    ...        }
    ...     )
    ... )["sum"]
    3.0
    """
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    return {"sum": data.sum()}
