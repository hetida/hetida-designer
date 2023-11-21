# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "scores": {"data_type": "SERIES"},
        "threshold": {"data_type": "FLOAT"},
    },
    "outputs": {
        "alerts": {"data_type": "SERIES"},
    },
    "name": "Alerts from Score",
    "category": "Anomaly Detection",
    "description": "Generate a Series indicating starts and ends of anomalous situations",
    "version_tag": "1.0.0",
    "id": "38f168ef-cb06-d89c-79b3-0cd823f32e9d",
    "revision_group_id": "38f168ef-cb06-d89c-79b3-0cd823f32e9d",
    "state": "RELEASED",
    "released_timestamp": "2022-02-09T17:33:29.236535+00:00",
}


def main(*, scores, threshold):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    alerts = (scores > threshold).astype(int).diff(1).fillna(0)
    alerts.name = "alerts"

    return {"alerts": alerts}


INITIAL_TEST_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "scores",
            "adapter_id": "direct_provisioning",
            "use_default_value": False,
            "filters": {
                "value": (
                    "{\n"
                    '    "2020-01-01T01:15:27.000Z": 42.2,\n'
                    '    "2020-01-03T08:20:03.000Z": 18.7,\n'
                    '    "2020-01-03T08:20:04.000Z": 25.9\n'
                    "}"
                )
            },
        },
        {
            "workflow_input_name": "threshold",
            "adapter_id": "direct_provisioning",
            "use_default_value": False,
            "filters": {"value": "30"},
        },
    ],
}
