from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType  # add your own imports here


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"timeseries_data": DataType.Any}, outputs={"last_index": DataType.Any}
)
def main(*, timeseries_data):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    if len(timeseries_data) == 0:
        return {"last_index": None}

    return {"last_index": timeseries_data.index.max().to_pydatetime().isoformat()}
