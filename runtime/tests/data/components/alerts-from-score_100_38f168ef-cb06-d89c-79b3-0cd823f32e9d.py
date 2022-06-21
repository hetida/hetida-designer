# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {"scores": "SERIES", "threshold": "FLOAT"},
    "outputs": {"alerts": "SERIES"},
    "name": "Alerts from Score",
    "description": "Generate a Series indicating starts and ends of anomalous situations",
    "category": "Anomaly Detection",
    "id": "38f168ef-cb06-d89c-79b3-0cd823f32e9d",
    "revision_group_id": "38f168ef-cb06-d89c-79b3-0cd823f32e9d",
    "version_tag": "1.0.0",
}


def main(*, scores, threshold):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    alerts = (scores > threshold).astype(int).diff(1).fillna(0)
    alerts.name = "alerts"

    return {"alerts": alerts}
