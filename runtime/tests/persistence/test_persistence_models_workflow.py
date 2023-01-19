from copy import deepcopy

from hetdesrun.persistence.models.io import IOConnector
from hetdesrun.persistence.models.link import Link
from hetdesrun.persistence.models.operator import Operator
from hetdesrun.persistence.models.workflow import WorkflowContent
from hetdesrun.utils import get_uuid_from_seed

content_json = {
    "constants": [],
    "inputs": [
        {
            "id": str(get_uuid_from_seed("input")),
            "name": "wf_input",
            "data_type": "INT",
            "operator_id": str(get_uuid_from_seed("operator")),
            "connector_id": str(get_uuid_from_seed("operator input")),
            "operator_name": "operator",
            "connector_name": "operator_input",
            "position": {"x": 0, "y": 0},
        }
    ],
    "outputs": [
        {
            "id": str(get_uuid_from_seed("output")),
            "data_type": "INT",
            "name": "wf_output",
            "operator_id": str(get_uuid_from_seed("operator")),
            "connector_id": str(get_uuid_from_seed("operator output")),
            "operator_name": "operator",
            "connector_name": "operator_output",
            "position": {"x": 0, "y": 0},
        }
    ],
    "operators": [
        {
            "id": str(get_uuid_from_seed("operator")),
            "revision_group_id": str(get_uuid_from_seed("group of component 1")),
            "name": "operator",
            "type": "COMPONENT",
            "state": "RELEASED",
            "version_tag": "1.0.0",
            "transformation_id": str(get_uuid_from_seed("component 1")),
            "inputs": [
                {
                    "id": str(get_uuid_from_seed("operator input")),
                    "name": "operator_input",
                    "data_type": "INT",
                    "position": {"x": 0, "y": 0},
                },
            ],
            "outputs": [
                {
                    "id": str(get_uuid_from_seed("operator output")),
                    "name": "operator_output",
                    "data_type": "INT",
                    "position": {"x": 0, "y": 0},
                },
            ],
            "position": {"x": 0, "y": 0},
        }
    ],
    "links": [
        {
            "id": str(get_uuid_from_seed("link 1")),
            "start": {
                "connector": {
                    "id": str(get_uuid_from_seed("input")),
                    "name": "wf_input",
                    "data_type": "INT",
                    "position": {"x": 0, "y": 0},
                },
            },
            "end": {
                "operator": str(get_uuid_from_seed("operator")),
                "connector": {
                    "id": str(get_uuid_from_seed("operator input")),
                    "name": "operator_input",
                    "data_type": "INT",
                    "position": {"x": 0, "y": 0},
                },
            },
            "path": [],
        },
        {
            "id": str(get_uuid_from_seed("link 2")),
            "start": {
                "operator": str(get_uuid_from_seed("operator")),
                "connector": {
                    "id": str(get_uuid_from_seed("operator output")),
                    "name": "operator_output",
                    "data_type": "INT",
                    "position": {"x": 0, "y": 0},
                },
            },
            "end": {
                "connector": {
                    "id": str(get_uuid_from_seed("output")),
                    "name": "wf_output",
                    "data_type": "INT",
                    "position": {"x": 0, "y": 0},
                },
            },
            "path": [],
        },
    ],
}

content_json_wrong_output_connector_name = deepcopy(content_json)
content_json_wrong_output_connector_name["outputs"][0][
    "connector_name"
] = "connector_name"


def test_workflow_validator_determine_outputs_from_operators_and_links():
    assert (
        content_json_wrong_output_connector_name["outputs"][0]["connector_name"]
        == "connector_name"
    )
    content_generated_io = WorkflowContent(**content_json_wrong_output_connector_name)
    assert content_generated_io.outputs[0].connector_name == "operator_output"
