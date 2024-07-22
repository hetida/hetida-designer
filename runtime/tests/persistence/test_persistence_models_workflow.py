import json
import logging
import os
from copy import deepcopy

import pytest

from hetdesrun.persistence.models.workflow import WorkflowContent
from hetdesrun.utils import get_uuid_from_seed


@pytest.fixture()
def workflow_content_dict() -> dict:
    return {
        "constants": [
            {
                "connector_id": "15637612-6dc7-4f55-7b5b-83c9fdac8579",
                "connector_name": "series",
                "data_type": "SERIES",
                "id": "b44f8d11-73c2-4f52-bc56-ff738618fdbb",
                "name": None,
                "operator_id": "ea5479cb-a8df-4f8c-8165-86c21d0fd8e8",
                "operator_name": "Combine into DataFrame (2)",
                "position": {"x": 510, "y": 60},
                "value": (
                    '{\n    "2020-01-01T01:15:27.000Z": 42.2,\n    "2020-01-03T08:20:03.000Z": '
                    '18.7,\n    "2020-01-03T08:20:04.000Z": 25.9\n}'
                ),
            },
        ],
        "inputs": [
            {
                "connector_id": "15637612-6dc7-4f55-7b5b-83c9fdac8579",
                "connector_name": "series",
                "data_type": "SERIES",
                "id": "9f4b9299-867b-41fa-86f8-29069574c991",
                "name": "series_1",
                "operator_id": "f2e74579-6058-474a-bb9e-ae2d9a059b6d",
                "operator_name": "Combine into DataFrame",
                "position": {"x": 0, "y": 190},
                "type": "OPTIONAL",
                "value": {
                    "2020-01-01T01:15:27.000Z": 42.2,
                    "2020-01-03T08:20:03.000Z": 18.7,
                    "2020-01-03T08:20:04.000Z": 25.9,
                },
            },
            {
                "connector_id": "3e68b069-390e-cf1f-5916-101b7fe4cf4a",
                "connector_name": "series_or_dataframe",
                "data_type": "ANY",
                "id": "d36314d1-d09c-4af2-b472-bb46ce30b2ba",
                "name": "series_or_dataframe",
                "operator_id": "f2e74579-6058-474a-bb9e-ae2d9a059b6d",
                "operator_name": "Combine into DataFrame",
                "position": {"x": 0, "y": 220},
                "type": "REQUIRED",
                "value": None,
            },
        ],
        "links": [
            {
                "end": {
                    "connector": {
                        "data_type": "ANY",
                        "id": "3e68b069-390e-cf1f-5916-101b7fe4cf4a",
                        "name": "series_or_dataframe",
                        "position": {"x": 0, "y": 0},
                    },
                    "operator": "ea5479cb-a8df-4f8c-8165-86c21d0fd8e8",
                },
                "id": "0a460b44-34bc-42ac-9de8-04aac6f376a3",
                "path": [],
                "start": {
                    "connector": {
                        "data_type": "DATAFRAME",
                        "id": "cbf856b7-faf7-3079-d8e8-3b666d6f9d84",
                        "name": "dataframe",
                        "position": {"x": 0, "y": 0},
                    },
                    "operator": "f2e74579-6058-474a-bb9e-ae2d9a059b6d",
                },
            },
            {
                "end": {
                    "connector": {
                        "data_type": "SERIES",
                        "id": "15637612-6dc7-4f55-7b5b-83c9fdac8579",
                        "name": "series",
                        "position": {"x": 0, "y": 0},
                    },
                    "operator": "f2e74579-6058-474a-bb9e-ae2d9a059b6d",
                },
                "id": "c35302ff-e7c6-4558-b898-9dcb070040ab",
                "path": [],
                "start": {
                    "connector": {
                        "data_type": "SERIES",
                        "id": "9f4b9299-867b-41fa-86f8-29069574c991",
                        "name": "series_1",
                        "position": {"x": 0, "y": 190},
                    },
                    "operator": None,
                },
            },
            {
                "end": {
                    "connector": {
                        "data_type": "ANY",
                        "id": "3e68b069-390e-cf1f-5916-101b7fe4cf4a",
                        "name": "series_or_dataframe",
                        "position": {"x": 0, "y": 0},
                    },
                    "operator": "f2e74579-6058-474a-bb9e-ae2d9a059b6d",
                },
                "id": "529c5379-ab0f-4aaf-b978-3b6f4e664e30",
                "path": [],
                "start": {
                    "connector": {
                        "data_type": "ANY",
                        "id": "d36314d1-d09c-4af2-b472-bb46ce30b2ba",
                        "name": "series_or_dataframe",
                        "position": {"x": 0, "y": 220},
                    },
                    "operator": None,
                },
            },
            {
                "end": {
                    "connector": {
                        "data_type": "SERIES",
                        "id": "15637612-6dc7-4f55-7b5b-83c9fdac8579",
                        "name": "series",
                        "position": {"x": 0, "y": 0},
                    },
                    "operator": "ea5479cb-a8df-4f8c-8165-86c21d0fd8e8",
                },
                "id": "dddad71a-ae23-4812-b381-38ef6d90bd6a",
                "path": [],
                "start": {
                    "connector": {
                        "data_type": "SERIES",
                        "id": "b44f8d11-73c2-4f52-bc56-ff738618fdbb",
                        "name": None,
                        "position": {"x": 510, "y": 60},
                    },
                    "operator": None,
                },
            },
            {
                "end": {
                    "connector": {
                        "data_type": "DATAFRAME",
                        "id": "ebbfb57d-5108-4f75-9ea3-7025f31530f9",
                        "name": "dataframe",
                        "position": {"x": 1230, "y": 160},
                    },
                    "operator": None,
                },
                "id": "e614d1a7-118c-490c-b61f-2590bcaec254",
                "path": [],
                "start": {
                    "connector": {
                        "data_type": "DATAFRAME",
                        "id": "cbf856b7-faf7-3079-d8e8-3b666d6f9d84",
                        "name": "dataframe",
                        "position": {"x": 0, "y": 0},
                    },
                    "operator": "ea5479cb-a8df-4f8c-8165-86c21d0fd8e8",
                },
            },
        ],
        "operators": [
            {
                "id": "f2e74579-6058-474a-bb9e-ae2d9a059b6d",
                "inputs": [
                    {
                        "data_type": "SERIES",
                        "id": "15637612-6dc7-4f55-7b5b-83c9fdac8579",
                        "name": "series",
                        "position": {"x": 0, "y": 0},
                        "type": "REQUIRED",
                        "value": None,
                        "exposed": True,
                    },
                    {
                        "data_type": "ANY",
                        "id": "3e68b069-390e-cf1f-5916-101b7fe4cf4a",
                        "name": "series_or_dataframe",
                        "position": {"x": 0, "y": 0},
                        "type": "REQUIRED",
                        "value": None,
                        "exposed": True,
                    },
                ],
                "name": "Combine into DataFrame",
                "outputs": [
                    {
                        "data_type": "DATAFRAME",
                        "id": "cbf856b7-faf7-3079-d8e8-3b666d6f9d84",
                        "name": "dataframe",
                        "position": {"x": 0, "y": 0},
                    }
                ],
                "position": {"x": 250, "y": 130},
                "revision_group_id": "68f91351-a1f5-9959-414a-2c72003f3226",
                "state": "RELEASED",
                "transformation_id": "68f91351-a1f5-9959-414a-2c72003f3226",
                "type": "COMPONENT",
                "version_tag": "1.0.0",
            },
            {
                "id": "ea5479cb-a8df-4f8c-8165-86c21d0fd8e8",
                "inputs": [
                    {
                        "data_type": "SERIES",
                        "id": "15637612-6dc7-4f55-7b5b-83c9fdac8579",
                        "name": "series",
                        "position": {"x": 0, "y": 0},
                        "type": "REQUIRED",
                        "value": None,
                        "exposed": True,
                    },
                    {
                        "data_type": "ANY",
                        "id": "3e68b069-390e-cf1f-5916-101b7fe4cf4a",
                        "name": "series_or_dataframe",
                        "position": {"x": 0, "y": 0},
                        "type": "REQUIRED",
                        "value": None,
                        "exposed": True,
                    },
                ],
                "name": "Combine into DataFrame (2)",
                "outputs": [
                    {
                        "data_type": "DATAFRAME",
                        "id": "cbf856b7-faf7-3079-d8e8-3b666d6f9d84",
                        "name": "dataframe",
                        "position": {"x": 0, "y": 0},
                    }
                ],
                "position": {"x": 780, "y": 100},
                "revision_group_id": "68f91351-a1f5-9959-414a-2c72003f3226",
                "state": "RELEASED",
                "transformation_id": "68f91351-a1f5-9959-414a-2c72003f3226",
                "type": "COMPONENT",
                "version_tag": "1.0.0",
            },
        ],
        "outputs": [
            {
                "connector_id": "cbf856b7-faf7-3079-d8e8-3b666d6f9d84",
                "connector_name": "dataframe",
                "data_type": "DATAFRAME",
                "id": "ebbfb57d-5108-4f75-9ea3-7025f31530f9",
                "name": "dataframe",
                "operator_id": "ea5479cb-a8df-4f8c-8165-86c21d0fd8e8",
                "operator_name": "Combine into DataFrame (2)",
                "position": {"x": 1230, "y": 160},
            }
        ],
    }


def test_workflow_content_accepted(workflow_content_dict: dict) -> None:
    workflow_content = WorkflowContent(**workflow_content_dict)
    assert json.loads(workflow_content.json()) == workflow_content_dict


def test_workflow_content_validator_operator_names_unique(
    workflow_content_dict: dict,
) -> None:
    workflow_content_double_operator_name_dict = deepcopy(workflow_content_dict)
    workflow_content_double_operator_name_dict["operators"][1]["name"] = (
        workflow_content_double_operator_name_dict["operators"][0]["name"]
    )
    workflow_content_double_operator_name = WorkflowContent(
        **workflow_content_double_operator_name_dict
    )
    assert (
        workflow_content_double_operator_name.operators[1].name
        != workflow_content_double_operator_name.operators[0].name
    )

    workflow_content_single_operator_with_suffix_dict = deepcopy(workflow_content_dict)
    del workflow_content_single_operator_with_suffix_dict["operators"][0]
    del workflow_content_single_operator_with_suffix_dict["links"][2]
    del workflow_content_single_operator_with_suffix_dict["links"][1]
    del workflow_content_single_operator_with_suffix_dict["links"][0]
    workflow_content_single_operator_with_suffix = WorkflowContent(
        **workflow_content_single_operator_with_suffix_dict
    )
    assert len(workflow_content_single_operator_with_suffix.operators) == 1
    assert workflow_content_single_operator_with_suffix.operators[0].name.endswith("(2)") is False


def test_workflow_content_validator_link_connectors_match_operator_ios(
    caplog: pytest.LogCaptureFixture, workflow_content_dict: dict
) -> None:
    with caplog.at_level(logging.WARNING):
        workflow_content_with_inner_link_to_wrong_operator_id_dict = deepcopy(workflow_content_dict)
        workflow_content_with_inner_link_to_wrong_operator_id_dict["links"][0]["start"][
            "operator"
        ] = str(get_uuid_from_seed("wrong id"))
        caplog.clear()
        workflow_content_with_inner_link_to_wrong_operator_id = WorkflowContent(
            **workflow_content_with_inner_link_to_wrong_operator_id_dict
        )
        assert "Operator output" in caplog.text
        assert "not found" in caplog.text
        assert len(workflow_content_with_inner_link_to_wrong_operator_id.links) == 4

        workflow_content_with_output_link_to_wrong_operator_id_dict = deepcopy(
            workflow_content_dict
        )
        workflow_content_with_output_link_to_wrong_operator_id_dict["links"][4]["start"][
            "operator"
        ] = str(get_uuid_from_seed("wrong id"))
        caplog.clear()
        workflow_content_with_output_link_to_wrong_operator_id = WorkflowContent(
            **workflow_content_with_output_link_to_wrong_operator_id_dict
        )
        assert "Operator output" in caplog.text
        assert "not found" in caplog.text
        assert len(workflow_content_with_output_link_to_wrong_operator_id.links) == 4

        workflow_content_with_inner_link_non_matching_start_connector_dict = deepcopy(
            workflow_content_dict
        )
        workflow_content_with_inner_link_non_matching_start_connector_dict["links"][0]["start"][
            "connector"
        ]["name"] = "wrong_name"
        caplog.clear()
        workflow_content_with_inner_link_non_matching_start_connector = WorkflowContent(
            **workflow_content_with_inner_link_non_matching_start_connector_dict
        )
        assert "link start connector" in caplog.text
        assert "do not match" in caplog.text
        assert len(workflow_content_with_inner_link_non_matching_start_connector.links) == 4

        workflow_content_with_inner_link_from_wrong_operator_id_dict = deepcopy(
            workflow_content_dict
        )
        workflow_content_with_inner_link_from_wrong_operator_id_dict["links"][0]["end"][
            "operator"
        ] = str(get_uuid_from_seed("wrong id"))
        caplog.clear()
        workflow_content_with_inner_link_from_wrong_operator_id = WorkflowContent(
            **workflow_content_with_inner_link_from_wrong_operator_id_dict
        )
        assert "Operator input" in caplog.text
        assert "not found" in caplog.text
        assert len(workflow_content_with_inner_link_from_wrong_operator_id.links) == 4

        workflow_content_with_input_link_to_wrong_operator_id_dict = deepcopy(workflow_content_dict)
        workflow_content_with_input_link_to_wrong_operator_id_dict["links"][1]["end"][
            "operator"
        ] = str(get_uuid_from_seed("wrong id"))
        caplog.clear()
        workflow_content_with_input_link_to_wrong_operator_id = WorkflowContent(
            **workflow_content_with_input_link_to_wrong_operator_id_dict
        )
        assert "Operator input" in caplog.text
        assert "not found" in caplog.text
        assert len(workflow_content_with_input_link_to_wrong_operator_id.links) == 4

        workflow_content_with_inner_link_non_matching_end_connector_dict = deepcopy(
            workflow_content_dict
        )
        workflow_content_with_inner_link_non_matching_end_connector_dict["links"][0]["end"][
            "connector"
        ]["name"] = "wrong_name"
        caplog.clear()
        workflow_content_with_inner_link_non_matching_end_connector = WorkflowContent(
            **workflow_content_with_inner_link_non_matching_end_connector_dict
        )
        assert "link end connector" in caplog.text
        assert "do not match" in caplog.text
        assert len(workflow_content_with_inner_link_non_matching_end_connector.links) == 4

        workflow_content_with_inner_link_to_not_exposed_operator_input_dict = deepcopy(
            workflow_content_dict
        )
        workflow_content_with_inner_link_to_not_exposed_operator_input_dict["operators"][1][
            "inputs"
        ][1]["type"] = "OPTIONAL"
        workflow_content_with_inner_link_to_not_exposed_operator_input_dict["operators"][1][
            "inputs"
        ][1]["exposed"] = False
        caplog.clear()
        workflow_content_with_inner_link_to_not_exposed_operator_input = WorkflowContent(
            **workflow_content_with_inner_link_to_not_exposed_operator_input_dict
        )
        assert "not exposed operator input" in caplog.text
        assert len(workflow_content_with_inner_link_to_not_exposed_operator_input.links) == 4


def test_validator_links_acyclic_directed_graph() -> None:
    pass


def test_validator_clean_up_workflow_content_inputs(
    caplog: pytest.LogCaptureFixture, workflow_content_dict: dict
) -> None:
    with caplog.at_level(logging.WARNING):
        workflow_content_with_input_referencing_wrong_operator_dict = deepcopy(
            workflow_content_dict
        )
        workflow_content_with_input_referencing_wrong_operator_dict["inputs"][0]["operator_id"] = (
            str(get_uuid_from_seed("wrong id"))
        )
        caplog.clear()
        WorkflowContent(**workflow_content_with_input_referencing_wrong_operator_dict)
        assert "Operator input" in caplog.text
        assert "not found" in caplog.text

        workflow_content_with_input_not_matching_referenced_operator_dict = deepcopy(
            workflow_content_dict
        )
        workflow_content_with_input_not_matching_referenced_operator_dict["inputs"][0][
            "data_type"
        ] = "STRING"
        caplog.clear()
        WorkflowContent(**workflow_content_with_input_not_matching_referenced_operator_dict)
        assert "Operator input" in caplog.text
        assert "does not match" in caplog.text

        workflow_content_with_input_referencing_not_exposed_operator_input_dict = deepcopy(
            workflow_content_dict
        )
        caplog.clear()
        workflow_content_with_input_referencing_not_exposed_operator_input_dict["operators"][0][
            "inputs"
        ][0]["type"] = "OPTIONAL"
        workflow_content_with_input_referencing_not_exposed_operator_input_dict["operators"][0][
            "inputs"
        ][0]["exposed"] = False
        WorkflowContent(**workflow_content_with_input_referencing_not_exposed_operator_input_dict)
        assert "Operator input" in caplog.text
        assert "is not exposed" in caplog.text

        workflow_content_with_unlinked_named_input_dict = deepcopy(workflow_content_dict)
        workflow_content_with_unlinked_named_input_dict["inputs"][0]["id"] = str(
            get_uuid_from_seed("wrong id")
        )
        del workflow_content_with_unlinked_named_input_dict["links"][1]
        caplog.clear()
        WorkflowContent(**workflow_content_with_unlinked_named_input_dict)
        assert "Link" in caplog.text
        assert "not found" in caplog.text

        workflow_content_with_input_not_matching_link_start_connector_dict = deepcopy(
            workflow_content_dict
        )
        workflow_content_with_input_not_matching_link_start_connector_dict["inputs"][0]["name"] = (
            "wrong_name"
        )
        caplog.clear()
        WorkflowContent(**workflow_content_with_input_not_matching_link_start_connector_dict)
        assert "Link start connector" in caplog.text
        assert "does not match" in caplog.text

        workflow_content_with_changed_input_position_dict = deepcopy(workflow_content_dict)
        workflow_content_with_changed_input_position_dict["inputs"][0]["position"] = {
            "x": 20,
            "y": 30,
        }
        caplog.clear()
        workflow_content_with_changed_input_position = WorkflowContent(
            **workflow_content_with_changed_input_position_dict
        )
        assert "position of the link start connector" in caplog.text
        assert "does not match" in caplog.text
        assert workflow_content_with_changed_input_position.inputs[0].position.x == 20
        assert workflow_content_with_changed_input_position.inputs[0].position.y == 30

        workflow_content_with_input_linked_to_wrong_operator_input_dict = deepcopy(
            workflow_content_dict
        )
        workflow_content_with_input_linked_to_wrong_operator_input_dict["inputs"][0][
            "operator_id"
        ] = "ea5479cb-a8df-4f8c-8165-86c21d0fd8e8"
        workflow_content_with_input_linked_to_wrong_operator_input_dict["inputs"][0][
            "connector_id"
        ] = "15637612-6dc7-4f55-7b5b-83c9fdac8579"
        del workflow_content_with_input_linked_to_wrong_operator_input_dict["links"][3]
        caplog.clear()
        WorkflowContent(**workflow_content_with_input_linked_to_wrong_operator_input_dict)
        assert "Link" in caplog.text
        assert "referencing different operator input" in caplog.text


def test_validator_clean_up_workflow_content_outputs(
    caplog: pytest.LogCaptureFixture, workflow_content_dict: dict
) -> None:
    with caplog.at_level(logging.WARNING):
        workflow_content_with_output_referencing_wrong_operator_dict = deepcopy(
            workflow_content_dict
        )
        workflow_content_with_output_referencing_wrong_operator_dict["outputs"][0][
            "operator_id"
        ] = str(get_uuid_from_seed("wrong id"))
        caplog.clear()
        WorkflowContent(**workflow_content_with_output_referencing_wrong_operator_dict)
        assert "Operator output" in caplog.text
        assert "not found" in caplog.text

        workflow_content_with_output_not_matching_referenced_operator_dict = deepcopy(
            workflow_content_dict
        )
        workflow_content_with_output_not_matching_referenced_operator_dict["outputs"][0][
            "data_type"
        ] = "STRING"
        caplog.clear()
        WorkflowContent(**workflow_content_with_output_not_matching_referenced_operator_dict)
        assert "Operator output" in caplog.text
        assert "does not match" in caplog.text

        workflow_content_with_unlinked_named_output_dict = deepcopy(workflow_content_dict)
        workflow_content_with_unlinked_named_output_dict["outputs"][0]["id"] = str(
            get_uuid_from_seed("wrong id")
        )
        del workflow_content_with_unlinked_named_output_dict["links"][4]
        caplog.clear()
        WorkflowContent(**workflow_content_with_unlinked_named_output_dict)
        assert "Link" in caplog.text
        assert "not found" in caplog.text

        workflow_content_with_output_not_matching_link_end_connector_dict = deepcopy(
            workflow_content_dict
        )
        workflow_content_with_output_not_matching_link_end_connector_dict["outputs"][0]["name"] = (
            "wrong_name"
        )
        caplog.clear()
        WorkflowContent(**workflow_content_with_output_not_matching_link_end_connector_dict)
        assert "Link end connector" in caplog.text
        assert "does not match" in caplog.text

        workflow_content_with_changed_output_position_dict = deepcopy(workflow_content_dict)
        workflow_content_with_changed_output_position_dict["outputs"][0]["position"] = {
            "x": 20,
            "y": 30,
        }
        caplog.clear()
        workflow_content_with_changed_output_position = WorkflowContent(
            **workflow_content_with_changed_output_position_dict
        )
        assert "position of the link end connector" in caplog.text
        assert "does not match" in caplog.text
        assert workflow_content_with_changed_output_position.outputs[0].position.x == 20
        assert workflow_content_with_changed_output_position.outputs[0].position.y == 30

        workflow_content_with_output_linked_to_wrong_operator_output_dict = deepcopy(
            workflow_content_dict
        )
        workflow_content_with_output_linked_to_wrong_operator_output_dict["outputs"][0][
            "operator_id"
        ] = "f2e74579-6058-474a-bb9e-ae2d9a059b6d"
        workflow_content_with_output_linked_to_wrong_operator_output_dict["outputs"][0][
            "connector_id"
        ] = "cbf856b7-faf7-3079-d8e8-3b666d6f9d84"
        del workflow_content_with_output_linked_to_wrong_operator_output_dict["links"][0]
        caplog.clear()
        WorkflowContent(**workflow_content_with_output_linked_to_wrong_operator_output_dict)
        assert "Link" in caplog.text
        assert "referencing different operator output" in caplog.text


def test_validator_add_workflow_content_inputs_for_unlinked_operator_inputs(
    caplog: pytest.LogCaptureFixture, workflow_content_dict: dict
) -> None:
    workflow_content_with_unlinked_not_exposed_operator_input_dict = deepcopy(workflow_content_dict)
    del workflow_content_with_unlinked_not_exposed_operator_input_dict["constants"][0]
    del workflow_content_with_unlinked_not_exposed_operator_input_dict["links"][3]
    workflow_content_with_unlinked_not_exposed_operator_input_dict["operators"][1]["inputs"][0][
        "type"
    ] = "OPTIONAL"
    workflow_content_with_unlinked_not_exposed_operator_input_dict["operators"][1]["inputs"][0][
        "exposed"
    ] = False
    caplog.clear()
    workflow_content_with_unlinked_not_exposed_operator_input = WorkflowContent(
        **workflow_content_with_unlinked_not_exposed_operator_input_dict
    )
    assert caplog.text == ""
    assert len(workflow_content_with_unlinked_not_exposed_operator_input.inputs) == len(
        workflow_content_with_unlinked_not_exposed_operator_input_dict["inputs"]
    )
    assert len(workflow_content_with_unlinked_not_exposed_operator_input.constants) == len(
        workflow_content_with_unlinked_not_exposed_operator_input_dict["constants"]
    )

    workflow_content_with_unlinked_op_input_without_wf_input_dict = deepcopy(workflow_content_dict)
    del workflow_content_with_unlinked_op_input_without_wf_input_dict["constants"][0]
    del workflow_content_with_unlinked_op_input_without_wf_input_dict["links"][3]
    caplog.clear()
    workflow_content_with_unlinked_operator_input = WorkflowContent(
        **workflow_content_with_unlinked_op_input_without_wf_input_dict
    )
    assert "Found no workflow" in caplog.text
    assert "input and no link" in caplog.text
    assert len(workflow_content_with_unlinked_op_input_without_wf_input_dict["inputs"]) == 2
    assert len(workflow_content_with_unlinked_op_input_without_wf_input_dict["constants"]) == 0
    assert len(workflow_content_with_unlinked_operator_input.inputs) == 3
    assert len(workflow_content_with_unlinked_operator_input.constants) == 0

    workflow_content_with_linked_op_input_without_wf_input_dict = deepcopy(workflow_content_dict)
    del workflow_content_with_linked_op_input_without_wf_input_dict["inputs"][1]
    caplog.clear()
    workflow_content_with_linked_op_input_without_wf_input = WorkflowContent(
        **workflow_content_with_linked_op_input_without_wf_input_dict
    )
    assert "Found no workflow" in caplog.text
    assert "input but a link" in caplog.text
    assert len(workflow_content_with_linked_op_input_without_wf_input_dict["inputs"]) == 1
    assert len(workflow_content_with_linked_op_input_without_wf_input_dict["constants"]) == 1
    assert len(workflow_content_with_linked_op_input_without_wf_input.inputs) == 2
    assert len(workflow_content_with_linked_op_input_without_wf_input.constants) == 1


def test_validator_add_workflow_content_outputs_for_unlinked_operator_outputs(
    caplog: pytest.LogCaptureFixture, workflow_content_dict: dict
) -> None:
    workflow_content_with_unlinked_op_output_without_wf_output_dict = deepcopy(
        workflow_content_dict
    )
    del workflow_content_with_unlinked_op_output_without_wf_output_dict["outputs"][0]
    del workflow_content_with_unlinked_op_output_without_wf_output_dict["links"][4]
    caplog.clear()
    workflow_content_with_unlinked_operator_output = WorkflowContent(
        **workflow_content_with_unlinked_op_output_without_wf_output_dict
    )
    assert "Found no workflow" in caplog.text
    assert "output and no link" in caplog.text
    assert len(workflow_content_with_unlinked_op_output_without_wf_output_dict["outputs"]) == 0
    assert len(workflow_content_with_unlinked_operator_output.outputs) == 1

    workflow_content_with_linked_op_output_without_wf_output_dict = deepcopy(workflow_content_dict)
    del workflow_content_with_linked_op_output_without_wf_output_dict["outputs"][0]
    caplog.clear()
    workflow_content_with_linked_op_output_without_wf_output = WorkflowContent(
        **workflow_content_with_linked_op_output_without_wf_output_dict
    )
    assert "Found no workflow" in caplog.text
    assert "output but a link" in caplog.text
    assert len(workflow_content_with_linked_op_output_without_wf_output_dict["outputs"]) == 0
    assert len(workflow_content_with_linked_op_output_without_wf_output.outputs) == 1


def test_validator_clean_up_outer_links(
    caplog: pytest.LogCaptureFixture, workflow_content_dict: dict
) -> None:
    workflow_content_with_link_without_wf_input_dict = deepcopy(workflow_content_dict)
    workflow_content_with_link_without_wf_input_dict["inputs"][0]["id"] = get_uuid_from_seed(
        "wrong id"
    )
    caplog.clear()
    workflow_content_with_link_without_wf_input = WorkflowContent(
        **workflow_content_with_link_without_wf_input_dict
    )
    assert "Workflow input" in caplog.text
    assert "not found" in caplog.text
    assert len(workflow_content_with_link_without_wf_input_dict["links"]) == 5
    assert len(workflow_content_with_link_without_wf_input.links) == 4

    workflow_content_with_link_with_wf_input_without_name_dict = deepcopy(workflow_content_dict)
    del workflow_content_with_link_with_wf_input_without_name_dict["inputs"][0]["name"]
    caplog.clear()
    workflow_content_with_link_with_wf_input_without_name = WorkflowContent(
        **workflow_content_with_link_with_wf_input_without_name_dict
    )
    assert "Workflow input" in caplog.text
    assert "has no name" in caplog.text
    assert len(workflow_content_with_link_with_wf_input_without_name_dict["links"]) == 5
    assert len(workflow_content_with_link_with_wf_input_without_name.links) == 4

    workflow_content_with_link_without_wf_output_dict = deepcopy(workflow_content_dict)
    workflow_content_with_link_without_wf_output_dict["outputs"][0]["id"] = get_uuid_from_seed(
        "wrong id"
    )
    caplog.clear()
    workflow_content_with_link_without_wf_output = WorkflowContent(
        **workflow_content_with_link_without_wf_output_dict
    )
    assert "Workflow output" in caplog.text
    assert "not found" in caplog.text
    assert len(workflow_content_with_link_without_wf_output_dict["links"]) == 5
    assert len(workflow_content_with_link_without_wf_output.links) == 4

    workflow_content_with_link_with_wf_output_without_name_dict = deepcopy(workflow_content_dict)
    del workflow_content_with_link_with_wf_output_without_name_dict["outputs"][0]["name"]
    caplog.clear()
    workflow_content_with_link_with_wf_output_without_name = WorkflowContent(
        **workflow_content_with_link_with_wf_output_without_name_dict
    )
    assert "Workflow output" in caplog.text
    assert "has no name" in caplog.text
    assert len(workflow_content_with_link_with_wf_output_without_name_dict["links"]) == 5
    assert len(workflow_content_with_link_with_wf_output_without_name.links) == 4


def test_workflow_content_validation_for_delete_operator_linked_to_dynamic_workflow_input(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with open(
        os.path.join(
            "transformations",
            "workflows",
            "connectors",
            "combine-two-series-into-dataframe_100_09b29726-4373-4652-82c8-7aa3e3f91676.json",
        ),
        encoding="utf8",
    ) as f:
        workflow_content = json.load(f)["content"]

    workflow_content_deleted_operator_linked_with_workflow_inputs_dict = deepcopy(workflow_content)
    deleted_operator_id = workflow_content_deleted_operator_linked_with_workflow_inputs_dict[
        "operators"
    ][1]["id"]
    # operator f2e
    del workflow_content_deleted_operator_linked_with_workflow_inputs_dict["operators"][1]
    # link from workflow input d36 to operator #1 f2e input 3e6
    del workflow_content_deleted_operator_linked_with_workflow_inputs_dict["links"][2]
    # link from workflow input 9f4 to operator #1 f2e input 156
    del workflow_content_deleted_operator_linked_with_workflow_inputs_dict["links"][1]
    # link from operator f2e output cbf to operator #0 ea5 input 3e6
    del workflow_content_deleted_operator_linked_with_workflow_inputs_dict["links"][0]
    resulting_workflow_content = WorkflowContent(
        **workflow_content_deleted_operator_linked_with_workflow_inputs_dict
    )

    # The operator has to inputs and one output
    assert "Operator input referenced by dynamic workflow input '9f4" in caplog.text
    # workflow input #1
    assert "Operator input referenced by dynamic workflow input 'd36" in caplog.text
    # workflow input #2
    assert "not found! The input will be removed." in caplog.text
    # Removed link #0 between the deleted operator #1 f2e output and another operator #0 ea5 input
    assert "Found no workflow content input and no link end connector for operator" in caplog.text
    assert "Add unnamed workflow content input." in caplog.text

    assert (
        len(
            [
                wf_input
                for wf_input in resulting_workflow_content.inputs
                if str(wf_input.operator_id) == deleted_operator_id
            ]
        )
        == 0
    )


def test_workflow_content_validation_for_change_dynamic_input_to_constant() -> None:
    with open(
        os.path.join(
            "transformations",
            "workflows",
            "connectors",
            "combine-two-series-into-dataframe_100_09b29726-4373-4652-82c8-7aa3e3f91676.json",
        ),
        encoding="utf8",
    ) as f:
        workflow_content = json.load(f)["content"]

    workflow_content_with_changed_dynamic_input_to_constant_dict = deepcopy(workflow_content)
    workflow_content_with_changed_dynamic_input_to_constant_dict["constants"] = [
        workflow_content_with_changed_dynamic_input_to_constant_dict["inputs"][0]
    ]
    del workflow_content_with_changed_dynamic_input_to_constant_dict["inputs"][0]
    del workflow_content_with_changed_dynamic_input_to_constant_dict["constants"][0]["name"]
    workflow_content_with_changed_dynamic_input_to_constant_dict["constants"][0]["value"] = ""
    del workflow_content_with_changed_dynamic_input_to_constant_dict["links"][3]["start"][
        "connector"
    ]["name"]
    resulting_workflow_content = WorkflowContent(
        **workflow_content_with_changed_dynamic_input_to_constant_dict
    )
    assert len(resulting_workflow_content.constants) == 1
    assert len(resulting_workflow_content.inputs) == 2
