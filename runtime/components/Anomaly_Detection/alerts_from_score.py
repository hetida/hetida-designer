from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType  # add your own imports here


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"scores": DataType.Series, "threshold": DataType.Float},
    outputs={"alerts": DataType.Series},
)
def main(*, scores, threshold):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    alerts = (scores > threshold).astype(int).diff(1).fillna(0)
    alerts.name = "alerts"

    return {"alerts": alerts}
