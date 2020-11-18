from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType  # add your own imports here


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"timeseries_data": DataType.Any}, outputs={"first_index": DataType.Any}
)
def main(*, timeseries_data):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    if len(timeseries_data) == 0:
        return {"first_index": None}

    return {"first_index": timeseries_data.index.min().to_pydatetime().isoformat()}
