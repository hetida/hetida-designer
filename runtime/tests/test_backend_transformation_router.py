import json
import logging
from copy import deepcopy
from posixpath import join as posix_urljoin
from unittest import mock
from uuid import UUID

import pytest
from fastapi import HTTPException

from hetdesrun.component.code import expand_code, update_code
from hetdesrun.models.execution import ExecByIdInput, ExecLatestByGroupIdInput
from hetdesrun.models.wiring import InputWiring, WorkflowWiring
from hetdesrun.persistence.dbservice.nesting import update_or_create_nesting
from hetdesrun.persistence.dbservice.revision import (
    get_multiple_transformation_revisions,
    read_single_transformation_revision,
    store_single_transformation_revision,
)
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.trafoutils.filter.params import FilterParams
from hetdesrun.trafoutils.io.load import (
    load_json,
    transformation_revision_from_python_code,
)
from hetdesrun.utils import State, get_uuid_from_seed
from hetdesrun.webservice.config import get_config

tr_json_component_1 = {
    "id": str(get_uuid_from_seed("component 1")),
    "revision_group_id": str(get_uuid_from_seed("group of component 1")),
    "name": "component 0",
    "description": "description of component 0",
    "category": "category",
    "documentation": "documentation",
    "type": "COMPONENT",
    "state": "DRAFT",
    "version_tag": "1.0.0",
    "io_interface": {
        "inputs": [
            {
                "id": str(get_uuid_from_seed("operator input")),
                "name": "operator_input",
                "data_type": "INT",
                "type": "REQUIRED",
            }
        ],
        "outputs": [
            {
                "id": str(get_uuid_from_seed("operator output")),
                "name": "operator_output",
                "data_type": "INT",
            }
        ],
    },
    "content": 'from hetdesrun.component.registration import register\nfrom hetdesrun.datatypes import DataType\n\n\n# ***** DO NOT EDIT LINES BELOW *****\n# These lines may be overwritten if component details or inputs/outputs change.\n@register(\n    inputs={"operator_input": DataType.Integer},\n    outputs={"operator_output": DataType.Integer},\n    component_name="Pass Through Integer",\n    description="Just outputs its input value",\n    category="Connectors",\n    uuid="57eea09f-d28e-89af-4e81-2027697a3f0f",\n    group_id="57eea09f-d28e-89af-4e81-2027697a3f0f",\n    tag="1.0.0",\n)\ndef main(*, input):\n    # entrypoint function for this component\n    # ***** DO NOT EDIT LINES ABOVE *****\n    # write your function code here.\n\n    return {"operator_output": operator_input}\n',  # noqa: E501
    "test_wiring": {
        "input_wirings": [
            {
                "workflow_input_name": "operator_input",
                "adapter_id": "direct_provisioning",
                "use_default_value": False,
                "filters": {"value": "100"},
            },
        ],
        "output_wirings": [
            {
                "workflow_output_name": "operator_output",
                "adapter_id": "direct_provisioning",
                "filters": {},
            },
        ],
        "dashboard_positionings": [],
    },
}
tr_json_component_1_new_revision = {
    "id": str(get_uuid_from_seed("component 1 new revision")),
    "revision_group_id": str(get_uuid_from_seed("group of component 1")),
    "name": "component 0",
    "description": "description of component 0",
    "category": "category",
    "documentation": "documentation",
    "type": "COMPONENT",
    "state": "DRAFT",
    "version_tag": "1.0.1",
    "io_interface": {
        "inputs": [
            {
                "id": str(get_uuid_from_seed("operator input")),
                "name": "operator_input",
                "data_type": "INT",
                "type": "REQUIRED",
            }
        ],
        "outputs": [
            {
                "id": str(get_uuid_from_seed("operator output")),
                "name": "operator_output",
                "data_type": "STRING",
            }
        ],
    },
    "content": 'from hetdesrun.component.registration import register\nfrom hetdesrun.datatypes import DataType\n\n# ***** DO NOT EDIT LINES BELOW *****\n# These lines may be overwritten if component details or inputs/outputs change.\n@register(\n    inputs={"operator_input": DataType.Integer},\n    outputs={"operator_output": DataType.Integer},\n    component_name="Pass Through Integer",\n    description="Just outputs its input value",\n    category="Connectors",\n    uuid="57eea09f-d28e-89af-4e81-2027697a3f0f",\n    group_id="57eea09f-d28e-89af-4e81-2027697a3f0f",\n    tag="1.0.0"\n)\ndef main(*, input):\n    # entrypoint function for this component\n    # ***** DO NOT EDIT LINES ABOVE *****\n    # write your function code here.\n\n    return {"operator_output": operator_input}\n',  # noqa: E501
    "test_wiring": {
        "input_wirings": [
            {
                "workflow_input_name": "operator_input",
                "adapter_id": "direct_provisioning",
                "use_default_value": False,
                "filters": {"value": "100"},
            },
        ],
        "output_wirings": [
            {
                "workflow_output_name": "operator_output",
                "adapter_id": "direct_provisioning",
                "filters": {},
            },
        ],
        "dashboard_positionings": [],
    },
}
tr_json_component_2 = {
    "id": str(get_uuid_from_seed("component 2")),
    "revision_group_id": str(get_uuid_from_seed("group of component 2")),
    "name": "component 2",
    "description": "description of component 2",
    "category": "category",
    "documentation": "documentation",
    "type": "COMPONENT",
    "state": "RELEASED",
    "released_timestamp": "2019-12-01T12:00:00+00:00",
    "version_tag": "1.0.0",
    "io_interface": {
        "inputs": [],
        "outputs": [],
    },
    "content": 'code="code"',
    "test_wiring": {
        "input_wirings": [],
        "output_wirings": [],
        "dashboard_positionings": [],
    },
}
tr_json_component_2_update = {
    "id": str(get_uuid_from_seed("component 2")),
    "revision_group_id": str(get_uuid_from_seed("group of component 2")),
    "name": "new name",
    "description": "description of component 2",
    "category": "Test",
    "documentation": "documentation",
    "type": "COMPONENT",
    "state": "RELEASED",
    "released_timestamp": "2019-12-01T12:00:00+00:00",
    "version_tag": "1.0.0",
    "io_interface": {
        "inputs": [],
        "outputs": [],
    },
    "content": 'code="code"',
    "test_wiring": {
        "input_wirings": [],
        "output_wirings": [],
        "dashboard_positionings": [],
    },
}
tr_json_component_2_deprecate = {
    "id": str(get_uuid_from_seed("component 2")),
    "revision_group_id": str(get_uuid_from_seed("group of component 2")),
    "name": "new name",
    "description": "description of component 2",
    "category": "Test",
    "documentation": "documentation",
    "type": "COMPONENT",
    "state": "DISABLED",
    "released_timestamp": "2019-12-01T12:00:00+00:00",
    "disabled_timestamp": "2023-08-03T12:00:00+00:00",
    "version_tag": "1.0.0",
    "io_interface": {
        "inputs": [],
        "outputs": [],
    },
    "content": 'code="code"',
    "test_wiring": {
        "input_wirings": [],
        "output_wirings": [],
        "dashboard_positionings": [],
    },
}

tr_json_component_3 = {
    "id": str(get_uuid_from_seed("component 3")),
    "revision_group_id": str(get_uuid_from_seed("group of component 3")),
    "name": "Test1",
    "description": "New created component test",
    "category": "Äpfel",
    "version_tag": "1.0.1",
    "state": "DRAFT",
    "type": "COMPONENT",
    "documentation": "# New Component/Workflow\n## Description\n## Inputs\n## Outputs\n## Details\n## Examples\n",  # noqa: E501
    "content": '# add your own imports here, e.g.\n# import pandas as pd\n# import numpy as np\n\n\n# ***** DO NOT EDIT LINES BELOW *****\n# These lines may be overwritten if component details or inputs/outputs change.\nCOMPONENT_INFO = {\n    "inputs": {\n        "new_input_1": "STRING",\n    },\n    "outputs": {\n        "new_output_1": "BOOLEAN",\n    },\n    "name": "Test1",\n    "category": "Äpfel",\n    "description": "New created component test",\n    "version_tag": "1.0.1",\n    "id": "977cbb10-ca82-4893-b062-6036f918344d",\n    "revision_group_id": "a7128772-9729-4519-bc55-540327641a0c",\n    "state": "DRAFT",\n}\n\n\ndef main(*, new_input_1):\n    # entrypoint function for this component\n    # ***** DO NOT EDIT LINES ABOVE *****\n    # write your function code here.\n    print "test"\n    pass',  # noqa: E501
    "io_interface": {
        "inputs": [
            {
                "id": "a980edcb-7ad3-49a2-a78d-bd8092fccb90",
                "name": "new_input_1",
                "data_type": "STRING",
                "type": "REQUIRED",
            }
        ],
        "outputs": [
            {
                "id": "e18f0cca-502b-4352-8a03-43d3b2ec4697",
                "name": "new_output_1",
                "data_type": "BOOLEAN",
            }
        ],
    },
    "test_wiring": {
        "input_wirings": [],
        "output_wirings": [],
        "dashboard_positionings": [],
    },
}

tr_json_component_3_publish = {
    "id": str(get_uuid_from_seed("component 3")),
    "revision_group_id": str(get_uuid_from_seed("group of component 3")),
    "name": "Test1",
    "description": "New created component test",
    "category": "Äpfel",
    "version_tag": "1.0.1",
    "state": "RELEASED",
    "released_timestamp": "2019-12-01T12:00:00+00:00",
    "type": "COMPONENT",
    "documentation": "# New Component/Workflow\n## Description\n## Inputs\n## Outputs\n## Details\n## Examples\n",  # noqa: E501
    "content": '# add your own imports here, e.g.\n# import pandas as pd\n# import numpy as np\n\n\n# ***** DO NOT EDIT LINES BELOW *****\n# These lines may be overwritten if component details or inputs/outputs change.\nCOMPONENT_INFO = {\n    "inputs": {\n        "new_input_1": "STRING",\n    },\n    "outputs": {\n        "new_output_1": "BOOLEAN",\n    },\n    "name": "Test1",\n    "category": "Äpfel",\n    "description": "New created component test",\n    "version_tag": "1.0.1",\n    "id": "977cbb10-ca82-4893-b062-6036f918344d",\n    "revision_group_id": "a7128772-9729-4519-bc55-540327641a0c",\n    "state": "DRAFT",\n}\n\n\ndef main(*, new_input_1):\n    # entrypoint function for this component\n    # ***** DO NOT EDIT LINES ABOVE *****\n    # write your function code here.\n    print "test"\n    pass',  # noqa: E501
    "io_interface": {
        "inputs": [
            {
                "id": "a980edcb-7ad3-49a2-a78d-bd8092fccb90",
                "name": "new_input_1",
                "data_type": "STRING",
            }
        ],
        "outputs": [
            {
                "id": "e18f0cca-502b-4352-8a03-43d3b2ec4697",
                "name": "new_output_1",
                "data_type": "BOOLEAN",
            }
        ],
    },
    "test_wiring": {
        "input_wirings": [],
        "output_wirings": [],
        "dashboard_positionings": [],
    },
}

tr_json_workflow_1 = {
    "id": str(get_uuid_from_seed("workflow 1")),
    "revision_group_id": str(get_uuid_from_seed("group of workflow 1")),
    "name": "workflow 1",
    "description": "description of workflow 1",
    "category": "category",
    "documentation": "documentation",
    "type": "WORKFLOW",
    "state": "DRAFT",
    "version_tag": "1.0.0",
    "io_interface": {
        "inputs": [],
        "outputs": [],
    },
    "content": {
        "constants": [],
        "inputs": [],
        "outputs": [],
        "operators": [],
        "links": [],
    },
    "test_wiring": {
        "input_wirings": [],
        "output_wirings": [],
        "dashboard_positionings": [],
    },
}

tr_json_workflow_2_no_operator = {
    "id": str(get_uuid_from_seed("workflow 2")),
    "revision_group_id": str(get_uuid_from_seed("group of workflow 2")),
    "name": "workflow 2",
    "description": "description of workflow 2",
    "category": "category",
    "documentation": "documentation",
    "type": "WORKFLOW",
    "state": "DRAFT",
    "version_tag": "1.0.0",
    "io_interface": {
        "inputs": [],
        "outputs": [],
    },
    "content": {
        "constants": [],
        "inputs": [],
        "outputs": [],
        "operators": [],
        "links": [],
    },
    "test_wiring": {
        "input_wirings": [],
        "output_wirings": [],
        "dashboard_positionings": [],
    },
}
tr_json_workflow_2_added_operator = {
    "id": str(get_uuid_from_seed("workflow 2")),
    "revision_group_id": str(get_uuid_from_seed("group of workflow 2")),
    "name": "workflow 2",
    "description": "description of workflow 2",
    "category": "category",
    "documentation": "documentation",
    "type": "WORKFLOW",
    "state": "DRAFT",
    "version_tag": "1.0.0",
    "io_interface": {
        "inputs": [],
        "outputs": [],
    },
    "content": {
        "constants": [],
        "inputs": [],
        "outputs": [],
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
        "links": [],
    },
    "test_wiring": {
        "input_wirings": [],
        "output_wirings": [],
        "dashboard_positionings": [],
    },
}
tr_json_workflow_2_added_io_for_operator = {
    "id": str(get_uuid_from_seed("workflow 2")),
    "revision_group_id": str(get_uuid_from_seed("group of workflow 2")),
    "name": "workflow 2",
    "description": "description of workflow 2",
    "category": "category",
    "documentation": "documentation",
    "type": "WORKFLOW",
    "state": "DRAFT",
    "version_tag": "1.0.0",
    "io_interface": {
        "inputs": [
            {
                "id": str(get_uuid_from_seed("input")),
                "data_type": "INT",
                "type": "REQUIRED",
            }
        ],
        "outputs": [
            {
                "id": str(get_uuid_from_seed("output")),
                "data_type": "INT",
            }
        ],
    },
    "content": {
        "constants": [],
        "inputs": [
            {
                "id": str(get_uuid_from_seed("input")),
                "data_type": "INT",
                "type": "REQUIRED",
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
                        "type": "REQUIRED",
                        "position": {"x": 0, "y": 0},
                        "exposed": True,
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
        "links": [],
    },
    "test_wiring": {
        "input_wirings": [],
        "output_wirings": [],
        "dashboard_positionings": [],
    },
}
tr_json_workflow_2_with_named_io_for_operator = {
    "id": str(get_uuid_from_seed("workflow 2")),
    "revision_group_id": str(get_uuid_from_seed("group of workflow 2")),
    "name": "workflow 2",
    "description": "description of workflow 2",
    "category": "category",
    "documentation": "documentation",
    "type": "WORKFLOW",
    "state": "DRAFT",
    "version_tag": "1.0.0",
    "io_interface": {
        "inputs": [
            {
                "id": str(get_uuid_from_seed("input")),
                "name": "wf_input",
                "data_type": "INT",
                "type": "REQUIRED",
            }
        ],
        "outputs": [
            {
                "id": str(get_uuid_from_seed("output")),
                "name": "wf_output",
                "data_type": "INT",
            }
        ],
    },
    "content": {
        "constants": [],
        "inputs": [
            {
                "id": str(get_uuid_from_seed("input")),
                "name": "wf_input",
                "data_type": "INT",
                "type": "REQUIRED",
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
                "name": "wf_output",
                "data_type": "INT",
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
                        "type": "REQUIRED",
                        "position": {"x": 0, "y": 0},
                        "exposed": True,
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
    },
    "test_wiring": {
        "input_wirings": [
            {
                "workflow_input_name": "wf_input",
                "adapter_id": "direct_provisioning",
                "use_default_value": False,
                "filters": {"value": "100"},
            },
        ],
        "output_wirings": [
            {
                "workflow_output_name": "wf_output",
                "adapter_id": "direct_provisioning",
                "filters": {},
            },
        ],
        "dashboard_positionings": [],
    },
}
tr_json_workflow_2_update = deepcopy(tr_json_workflow_2_with_named_io_for_operator)
tr_json_workflow_2_update["name"] = "new name"


@pytest.mark.asyncio
async def test_get_all_transformation_revisions_with_valid_db_entries(
    async_test_client, mocked_clean_test_db_session
):
    store_single_transformation_revision(TransformationRevision(**tr_json_component_1))
    store_single_transformation_revision(TransformationRevision(**tr_json_component_2))
    store_single_transformation_revision(TransformationRevision(**tr_json_workflow_1))
    store_single_transformation_revision(
        TransformationRevision(**tr_json_workflow_2_with_named_io_for_operator)
    )
    async with async_test_client as ac:
        response = await ac.get("/api/transformations/")

    assert response.status_code == 200
    assert response.json()[0] == tr_json_component_1
    assert response.json()[1] == tr_json_component_2
    assert response.json()[2] == tr_json_workflow_1
    assert response.json()[3] == tr_json_workflow_2_with_named_io_for_operator


@pytest.mark.asyncio
async def test_get_all_transformation_revisions_with_no_db_entries(
    async_test_client, mocked_clean_test_db_session
):
    async with async_test_client as ac:
        response = await ac.get("/api/transformations/")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_transformation_revisions_strip_wirings(
    async_test_client, mocked_clean_test_db_session
):
    """Tests the different ways of stripping wirings from the response"""
    tr_dict = deepcopy(tr_json_component_1)
    tr_dict["io_interface"]["inputs"].append(
        {
            "id": str(get_uuid_from_seed("operator input 2")),
            "name": "operator_input_2",
            "data_type": "INT",
            "type": "REQUIRED",
        }
    )
    tr_dict["test_wiring"]["input_wirings"].append(
        {
            "workflow_input_name": "operator_input_2",
            "ref_id": "some_ref_id",
            "adapter_id": "other",
            "use_default_value": False,
            "filters": {"value": "100"},
        },
    )
    tr = TransformationRevision(**tr_dict)

    # now has two input wirings:
    # * first with adapter_id "direct_provisioning"
    # * second with adapter_id "other"
    #
    # has one output wiring with adapter_id "direct_provisioning"

    store_single_transformation_revision(tr)
    async with async_test_client as ac:
        # default settings have no effect
        resp = await ac.get("/api/transformations/", params={})
        assert resp.status_code == 200
        resp_json = resp.json()
        assert len(resp_json) == 1
        assert TransformationRevision(**resp_json[0]) == tr

        # strip_wirings removes all wirings
        resp = await ac.get("/api/transformations/", params={"strip_wirings": True})
        assert resp.status_code == 200
        resp_json = resp.json()
        assert len(resp_json) == 1
        trafo_from_resp = TransformationRevision(**resp_json[0])
        assert trafo_from_resp != tr
        assert len(trafo_from_resp.test_wiring.input_wirings) == 0
        assert len(trafo_from_resp.test_wiring.output_wirings) == 0

        # strip_wirings_with_adapter_id removes only certain wirings
        resp = await ac.get(
            "/api/transformations/", params={"strip_wirings_with_adapter_id": "other"}
        )
        assert resp.status_code == 200
        resp_json = resp.json()
        assert len(resp_json) == 1
        trafo_from_resp = TransformationRevision(**resp_json[0])
        assert trafo_from_resp != tr
        assert len(trafo_from_resp.test_wiring.input_wirings) == 1
        assert trafo_from_resp.test_wiring.input_wirings[0].adapter_id == "direct_provisioning"
        assert len(trafo_from_resp.test_wiring.output_wirings) == 1
        assert trafo_from_resp.test_wiring.input_wirings[0].adapter_id == "direct_provisioning"

        # keep_only_wirings_with_adapter_id keeps only certain wirings
        resp = await ac.get(
            "/api/transformations/",
            params={"keep_only_wirings_with_adapter_id": "other"},
        )
        assert resp.status_code == 200
        resp_json = resp.json()
        assert len(resp_json) == 1
        trafo_from_resp = TransformationRevision(**resp_json[0])
        assert trafo_from_resp != tr
        assert len(trafo_from_resp.test_wiring.input_wirings) == 1
        assert trafo_from_resp.test_wiring.input_wirings[0].adapter_id == "other"
        assert len(trafo_from_resp.test_wiring.output_wirings) == 0

        # keep_only_wirings_with_adapter_id keeps only certain wirings
        # for components_as_code if expand_component_code is True
        resp = await ac.get(
            "/api/transformations/",
            params={
                "keep_only_wirings_with_adapter_id": "other",
                "components_as_code": True,
                "expand_component_code": True,
            },
        )
        assert resp.status_code == 200
        resp_json = resp.json()
        assert len(resp_json) == 1
        trafo_from_resp = transformation_revision_from_python_code(resp_json[0])
        assert trafo_from_resp != tr
        assert len(trafo_from_resp.test_wiring.input_wirings) == 1
        assert trafo_from_resp.test_wiring.input_wirings[0].adapter_id == "other"
        assert len(trafo_from_resp.test_wiring.output_wirings) == 0


@pytest.mark.asyncio
async def test_get_all_transformation_revisions_with_specified_state(
    async_test_client, mocked_clean_test_db_session
):
    store_single_transformation_revision(
        TransformationRevision(**tr_json_component_1)  # DRAFT
    )
    store_single_transformation_revision(
        TransformationRevision(**tr_json_component_2)  # RELEASED
    )
    store_single_transformation_revision(
        TransformationRevision(**tr_json_workflow_1)  # DRAFT
    )
    tr_workflow_2 = TransformationRevision(**tr_json_workflow_2_with_named_io_for_operator)
    tr_workflow_2.deprecate()
    store_single_transformation_revision(tr_workflow_2)  # DISABLED
    async with async_test_client as ac:
        response_draft = await ac.get("/api/transformations/", params={"state": "DRAFT"})
        response_released = await ac.get("/api/transformations/", params={"state": "RELEASED"})
        response_disabled = await ac.get("/api/transformations/", params={"state": "DISABLED"})
        response_foo = await ac.get("/api/transformations/", params={"state": "FOO"})

    assert response_draft.status_code == 200
    assert len(response_draft.json()) == 2
    assert response_draft.json()[0] == tr_json_component_1
    assert response_draft.json()[1] == tr_json_workflow_1
    assert response_released.status_code == 200
    assert len(response_released.json()) == 1
    assert response_released.json()[0] == tr_json_component_2
    assert response_disabled.status_code == 200
    assert len(response_disabled.json()) == 1
    assert response_disabled.json()[0]["id"] == tr_json_workflow_2_with_named_io_for_operator["id"]
    assert response_disabled.json()[0]["state"] == "DISABLED"
    assert response_foo.status_code == 422
    assert "not a valid enumeration member" in response_foo.json()["detail"][0]["msg"]


@pytest.mark.asyncio
async def test_get_all_transformation_revisions_with_specified_type(
    async_test_client, mocked_clean_test_db_session
):
    store_single_transformation_revision(
        TransformationRevision(**tr_json_component_1)  # DRAFT
    )
    store_single_transformation_revision(
        TransformationRevision(**tr_json_component_2)  # RELEASED
    )
    store_single_transformation_revision(
        TransformationRevision(**tr_json_workflow_1)  # DRAFT
    )
    store_single_transformation_revision(
        TransformationRevision(**tr_json_workflow_2_with_named_io_for_operator)  # DRAFT
    )

    async with async_test_client as ac:
        response_component = await ac.get("/api/transformations/", params={"type": "COMPONENT"})
        response_workflow = await ac.get("/api/transformations/", params={"type": "WORKFLOW"})
        response_foo = await ac.get("/api/transformations/", params={"type": "FOO"})

    assert response_component.status_code == 200
    assert len(response_component.json()) == 2
    assert response_component.json()[0] == tr_json_component_1
    assert response_component.json()[1] == tr_json_component_2
    assert response_workflow.status_code == 200
    assert len(response_workflow.json()) == 2
    assert response_workflow.json()[0] == tr_json_workflow_1
    assert response_workflow.json()[1] == tr_json_workflow_2_with_named_io_for_operator
    assert response_foo.status_code == 422
    assert "not a valid enumeration member" in response_foo.json()["detail"][0]["msg"]


@pytest.mark.asyncio
async def test_get_all_transformation_revisions_with_specified_category(
    async_test_client, mocked_clean_test_db_session
):
    store_single_transformation_revision(
        TransformationRevision(**tr_json_component_1)  # category
    )
    store_single_transformation_revision(
        TransformationRevision(**tr_json_component_3)  # Äpfel
    )
    store_single_transformation_revision(
        TransformationRevision(**tr_json_workflow_1)  # category
    )
    store_single_transformation_revision(
        TransformationRevision(**tr_json_workflow_2_with_named_io_for_operator)  # category
    )

    url = "/api/transformations/"
    async with async_test_client as ac:
        response_category = await ac.get(url, params={"category": "category"})
        response_aepfel = await ac.get(url, params={"category": "Äpfel"})
        response_single_quote = await ac.get(url, params={"category": "'"})

    assert response_category.status_code == 200
    assert len(response_category.json()) == 3
    assert response_category.json()[0] == tr_json_component_1
    assert response_category.json()[1] == tr_json_workflow_1
    assert response_category.json()[2] == tr_json_workflow_2_with_named_io_for_operator
    assert response_aepfel.status_code == 200
    assert len(response_aepfel.json()) == 1
    assert response_aepfel.json()[0] == tr_json_component_3
    assert response_single_quote.status_code == 422
    assert "string does not match regex" in response_single_quote.json()["detail"][0]["msg"]


@pytest.mark.asyncio
async def test_get_all_transformation_revisions_with_specified_category_prefix(
    async_test_client, mocked_clean_test_db_session
):
    store_single_transformation_revision(
        TransformationRevision(**tr_json_component_1)  # category
    )
    store_single_transformation_revision(
        TransformationRevision(**tr_json_component_3)  # Äpfel
    )
    store_single_transformation_revision(
        TransformationRevision(**tr_json_workflow_1)  # category
    )
    store_single_transformation_revision(
        TransformationRevision(**tr_json_workflow_2_with_named_io_for_operator)  # category
    )

    url = "/api/transformations/"
    async with async_test_client as ac:
        response_cat = await ac.get(url, params={"category_prefix": "cat"})
        response_aepfel = await ac.get(url, params={"category_prefix": "Äpfel"})
        response_single_quote = await ac.get(url, params={"category_prefix": "'"})

    assert response_cat.status_code == 200
    for trafo_json in response_cat.json():
        print(trafo_json["id"], trafo_json["name"], trafo_json["category"])
    assert len(response_cat.json()) == 3
    assert response_cat.json()[0] == tr_json_component_1
    assert response_cat.json()[1] == tr_json_workflow_1
    assert response_cat.json()[2] == tr_json_workflow_2_with_named_io_for_operator
    assert response_aepfel.status_code == 200
    assert len(response_aepfel.json()) == 1
    assert response_aepfel.json()[0] == tr_json_component_3
    assert response_single_quote.status_code == 422
    assert "string does not match regex" in response_single_quote.json()["detail"][0]["msg"]


@pytest.mark.asyncio
async def test_get_all_transformation_revisions_with_specified_revision_group_id(
    async_test_client, mocked_clean_test_db_session
):
    tr_component_1 = TransformationRevision(**tr_json_component_1)
    store_single_transformation_revision(tr_component_1)

    tr_component_1_new_revision = TransformationRevision(**tr_json_component_1_new_revision)
    store_single_transformation_revision(tr_component_1_new_revision)

    url = "/api/transformations/"
    async with async_test_client as ac:
        response_category = await ac.get(
            url, params={"revision_group_id": str(tr_component_1.revision_group_id)}
        )

    assert response_category.status_code == 200
    assert len(response_category.json()) == 2
    assert response_category.json()[0] == tr_json_component_1
    assert response_category.json()[1] == tr_json_component_1_new_revision


@pytest.mark.asyncio
async def test_get_all_transformation_revisions_with_specified_ids(
    async_test_client, mocked_clean_test_db_session
):
    store_single_transformation_revision(
        TransformationRevision(**tr_json_component_1)  # get_uuid_from_seed("component 1")
    )
    store_single_transformation_revision(
        TransformationRevision(**tr_json_component_2)  # get_uuid_from_seed("component 2")
    )
    store_single_transformation_revision(
        TransformationRevision(**tr_json_component_3)  # get_uuid_from_seed("component 3")
    )

    url = "/api/transformations/"
    async with async_test_client as ac:
        response_two_ids = await ac.get(
            url,
            params={
                "id": [
                    get_uuid_from_seed("component 1"),
                    get_uuid_from_seed("component 2"),
                ]
            },
        )
        response_no_ids = await ac.get(url, params={"ids": []})

    assert response_two_ids.status_code == 200
    assert len(response_two_ids.json()) == 2
    assert response_two_ids.json()[0] == tr_json_component_1
    assert response_two_ids.json()[1] == tr_json_component_2
    assert response_no_ids.status_code == 200
    assert len(response_no_ids.json()) == 3


@pytest.mark.asyncio
async def test_get_all_transformation_revisions_with_specified_names(
    async_test_client, mocked_clean_test_db_session
):
    store_single_transformation_revision(
        TransformationRevision(**tr_json_component_1)  # "component 0", "1.0.0"
    )
    store_single_transformation_revision(
        TransformationRevision(**tr_json_component_1_new_revision)  # "component 0", "1.0.1"
    )
    store_single_transformation_revision(
        TransformationRevision(**tr_json_component_2)  # "component 2", "1.0.0"
    )

    url = "/api/transformations/"
    async with async_test_client as ac:
        response_names = await ac.get(
            url,
            params={"name": ["component 0", "component 1"]},
        )
        response_empty_names = await ac.get(url, params={"name": []})

    assert response_names.status_code == 200
    assert len(response_names.json()) == 2
    assert response_names.json()[0] == tr_json_component_1
    assert response_names.json()[1] == tr_json_component_1_new_revision
    assert response_empty_names.status_code == 200
    assert len(response_empty_names.json()) == 3


@pytest.mark.asyncio
async def test_get_all_transformation_revisions_without_including_deprecated(
    async_test_client, mocked_clean_test_db_session
):
    store_single_transformation_revision(
        TransformationRevision(**tr_json_component_1)  # DRAFT
    )
    store_single_transformation_revision(
        TransformationRevision(**tr_json_component_2)  # RELEASED
    )
    store_single_transformation_revision(
        TransformationRevision(**tr_json_workflow_1)  # DRAFT
    )
    tr_workflow_2 = TransformationRevision(**tr_json_workflow_2_with_named_io_for_operator)
    tr_workflow_2.deprecate()
    store_single_transformation_revision(tr_workflow_2)  # DISABLED
    url = "/api/transformations/"
    async with async_test_client as ac:
        response_without_deprecated = await ac.get(
            url,
            params={"include_deprecated": False},
        )
        response_with_deprecated = await ac.get(url)

    assert response_without_deprecated.status_code == 200
    assert len(response_without_deprecated.json()) == 3
    assert response_without_deprecated.json()[0] == tr_json_component_1
    assert response_without_deprecated.json()[1] == tr_json_component_2
    assert response_without_deprecated.json()[2] == tr_json_workflow_1
    assert response_with_deprecated.status_code == 200
    assert len(response_with_deprecated.json()) == 4
    assert response_with_deprecated.json()[0] == tr_json_component_1
    assert response_with_deprecated.json()[1] == tr_json_component_2
    assert response_with_deprecated.json()[2] == tr_json_workflow_1
    assert (
        response_with_deprecated.json()[3]["id"]
        == tr_json_workflow_2_with_named_io_for_operator["id"]
    )


@pytest.mark.asyncio
async def test_get_all_transformation_revisions_including_dependencies(
    async_test_client, mocked_clean_test_db_session
):
    tr_component_1 = TransformationRevision(**tr_json_component_1)
    tr_component_1.deprecate()
    store_single_transformation_revision(tr_component_1)
    store_single_transformation_revision(
        TransformationRevision(**tr_json_workflow_2_with_named_io_for_operator)
    )
    url = "/api/transformations/"
    async with async_test_client as ac:
        response_without_dependencies = await ac.get(
            url,
            params={"type": "WORKFLOW"},
        )
        response_include_dependencies = await ac.get(
            url,
            params={"type": "WORKFLOW", "include_dependencies": True},
        )
        response_without_deprecated = await ac.get(
            url,
            params={"include_deprecated": False},
        )
        response_without_deprecated_include_dependencies = await ac.get(
            url,
            params={"include_dependencies": True, "include_deprecated": False},
        )

    assert response_without_dependencies.status_code == 200
    assert len(response_without_dependencies.json()) == 1
    assert response_include_dependencies.status_code == 200
    assert len(response_include_dependencies.json()) == 2
    assert response_without_deprecated.status_code == 200
    assert len(response_without_deprecated.json()) == 1
    assert response_without_deprecated_include_dependencies.status_code == 200
    assert len(response_without_deprecated_include_dependencies.json()) == 2


@pytest.mark.asyncio
async def test_get_all_transformation_revisions_with_combined_filters(
    async_test_client, mocked_clean_test_db_session
):
    store_single_transformation_revision(
        TransformationRevision(**tr_json_component_1)  # DRAFT
    )
    store_single_transformation_revision(
        TransformationRevision(**tr_json_component_2)  # RELEASED
    )
    store_single_transformation_revision(
        TransformationRevision(**tr_json_workflow_1)  # DRAFT
    )
    store_single_transformation_revision(
        TransformationRevision(**tr_json_workflow_2_with_named_io_for_operator)  # DRAFT
    )

    url = "/api/transformations/"
    async with async_test_client as ac:
        response_released_component = await ac.get(
            url,
            params={"type": "COMPONENT", "state": "RELEASED"},
        )
        response_draft_workflow = await ac.get(url, params={"type": "WORKFLOW", "state": "DRAFT"})

    assert response_released_component.status_code == 200
    assert len(response_released_component.json()) == 1
    assert response_released_component.json()[0] == tr_json_component_2
    assert response_draft_workflow.status_code == 200
    assert len(response_draft_workflow.json()) == 2
    assert response_draft_workflow.json()[0] == tr_json_workflow_1
    assert response_draft_workflow.json()[1] == tr_json_workflow_2_with_named_io_for_operator


@pytest.mark.asyncio
async def test_get_all_transformation_revisions_with_components_as_code(
    async_test_client, mocked_clean_test_db_session
):
    store_single_transformation_revision(
        TransformationRevision(**tr_json_component_1)  # DRAFT
    )
    store_single_transformation_revision(
        TransformationRevision(**tr_json_workflow_1)  # DRAFT
    )

    async with async_test_client as ac:
        response_components_as_code = await ac.get(
            "/api/transformations/", params={"components_as_code": True}
        )
        response_expand_component_code = await ac.get(
            "/api/transformations/", params={"expand_component_code": True}
        )
        response_both = await ac.get(
            "/api/transformations/",
            params={"components_as_code": True, "expand_component_code": True},
        )

    assert response_components_as_code.status_code == 200
    assert len(response_components_as_code.json()) == 2
    assert response_components_as_code.json()[0] == tr_json_workflow_1
    assert response_components_as_code.json()[1] == tr_json_component_1["content"]

    assert response_expand_component_code.status_code == 200
    assert len(response_expand_component_code.json()) == 2
    assert response_expand_component_code.json()[1] == tr_json_workflow_1
    assert tr_json_component_1["content"] in response_expand_component_code.json()[0]["content"]
    assert "TEST_WIRING_FROM_PY_FILE_IMPORT" in response_expand_component_code.json()[0]["content"]
    assert (
        '"""Documentation for component 0\n\ndocumentation\n"""\n\n'
        in response_expand_component_code.json()[0]["content"]
    )

    assert response_both.status_code == 200
    assert len(response_both.json()) == 2
    assert response_both.json()[0] == tr_json_workflow_1
    assert tr_json_component_1["content"] in response_both.json()[1]
    assert "TEST_WIRING_FROM_PY_FILE_IMPORT" in response_both.json()[1]

    assert '"""Documentation for component 0\n\ndocumentation\n"""\n\n' in response_both.json()[1]


@pytest.mark.asyncio
async def test_get_transformation_revision_by_id_with_component(
    async_test_client, mocked_clean_test_db_session
):
    store_single_transformation_revision(TransformationRevision(**tr_json_component_1))

    async with async_test_client as ac:
        response = await ac.get(
            posix_urljoin("/api/transformations/", str(get_uuid_from_seed("component 1")))
        )
    assert response.status_code == 200
    assert response.json() == tr_json_component_1


@pytest.mark.asyncio
async def test_get_transformation_revision_by_id_with_inexistent_component(
    async_test_client, mocked_clean_test_db_session
):
    async with async_test_client as ac:
        response = await ac.get(
            posix_urljoin(
                "/api/transformations/",
                str(get_uuid_from_seed("inexistent transformation revision")),
            )
        )
    assert response.status_code == 404
    assert "Found no" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_transformation_revision_by_id_with_workflow(
    async_test_client, mocked_clean_test_db_session
):
    store_single_transformation_revision(TransformationRevision(**tr_json_workflow_1))

    async with async_test_client as ac:
        response = await ac.get(
            posix_urljoin("/api/transformations/", str(get_uuid_from_seed("workflow 1")))
        )
    assert response.status_code == 200
    assert response.json() == tr_json_workflow_1


@pytest.mark.asyncio
async def test_get_transformation_revision_by_id_with_inexistent_workflow(
    async_test_client, mocked_clean_test_db_session
):
    async with async_test_client as ac:
        response = await ac.get(
            posix_urljoin(
                "/api/transformations/",
                str(get_uuid_from_seed("inexistent workflow")),
            )
        )
    assert response.status_code == 404
    assert "Found no" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_transformation_revision_with_workflow(
    async_test_client, mocked_clean_test_db_session
):
    store_single_transformation_revision(TransformationRevision(**tr_json_component_1))

    async with async_test_client as ac:
        response = await ac.post(
            "/api/transformations/",
            json=tr_json_workflow_2_with_named_io_for_operator,
        )

    assert response.status_code == 201
    assert response.json()["name"] == tr_json_workflow_2_with_named_io_for_operator["name"]


@pytest.mark.asyncio
async def test_update_transformation_revision_with_workflow(
    async_test_client, mocked_clean_test_db_session
):
    store_single_transformation_revision(TransformationRevision(**tr_json_component_1))
    store_single_transformation_revision(
        TransformationRevision(**tr_json_workflow_2_with_named_io_for_operator)
    )

    async with async_test_client as ac:
        response = await ac.put(
            posix_urljoin("/api/transformations/", str(get_uuid_from_seed("workflow 2"))),
            json=tr_json_workflow_2_update,
        )

    workflow_tr_in_db = read_single_transformation_revision(get_uuid_from_seed("workflow 2"))

    assert response.status_code == 201
    assert response.json()["name"] == "new name"
    assert len(workflow_tr_in_db.content.links) == 2


@pytest.mark.asyncio
async def test_update_transformation_revision_with_invalid_name_workflow(
    async_test_client, mocked_clean_test_db_session
):
    store_single_transformation_revision(TransformationRevision(**tr_json_component_1))
    store_single_transformation_revision(
        TransformationRevision(**tr_json_workflow_2_with_named_io_for_operator)
    )

    tr_json_workflow_2_update_invalid_name = deepcopy(tr_json_workflow_2_update)
    tr_json_workflow_2_update_invalid_name["name"] = "'"

    async with async_test_client as ac:
        response = await ac.put(
            posix_urljoin("/api/transformations/", str(get_uuid_from_seed("workflow 2"))),
            json=tr_json_workflow_2_update_invalid_name,
        )

    print(response.json())
    assert response.status_code == 422
    assert "string does not match regex" in response.json()["detail"][0]["msg"]
    assert "name" in response.json()["detail"][0]["loc"]


@pytest.mark.asyncio
async def test_update_transformation_revision_with_non_existing_workflow(
    async_test_client, mocked_clean_test_db_session
):
    store_single_transformation_revision(TransformationRevision(**tr_json_component_1))

    async with async_test_client as ac:
        response = await ac.put(
            posix_urljoin("/api/transformations/", str(get_uuid_from_seed("workflow 2"))),
            json=tr_json_workflow_2_update,
        )

    workflow_tr_in_db = read_single_transformation_revision(get_uuid_from_seed("workflow 2"))

    assert response.status_code == 201
    assert response.json()["name"] == "new name"
    assert len(workflow_tr_in_db.content.links) == 2


@pytest.mark.asyncio
async def test_update_transformation_revision_with_released_component(
    async_test_client, mocked_clean_test_db_session
):
    store_single_transformation_revision(TransformationRevision(**tr_json_component_2))

    async with async_test_client as ac:
        response = await ac.put(
            posix_urljoin("/api/transformations/", str(get_uuid_from_seed("component 2"))),
            json=tr_json_component_2_update,
        )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_transformation_revision_with_released_component_and_allow_overwrite_flag(
    async_test_client, mocked_clean_test_db_session
):
    store_single_transformation_revision(TransformationRevision(**tr_json_component_2))

    async with async_test_client as ac:
        response = await ac.put(
            posix_urljoin("/api/transformations/", str(get_uuid_from_seed("component 2"))),
            params={"allow_overwrite_released": True},
            json=tr_json_component_2_update,
        )

    assert response.status_code == 201
    assert response.json()["name"] == "new name"
    assert response.json()["category"] == "Test"


@pytest.mark.asyncio
async def test_update_transformation_revision_by_adding_operator_to_workflow_followed_by_get(
    async_test_client, mocked_clean_test_db_session
):
    store_single_transformation_revision(TransformationRevision(**tr_json_component_1))
    store_single_transformation_revision(TransformationRevision(**tr_json_workflow_2_no_operator))

    async with async_test_client as ac:
        put_response = await ac.put(
            posix_urljoin("/api/transformations/", str(get_uuid_from_seed("workflow 2"))),
            json=tr_json_workflow_2_added_operator,
        )
        get_response = await ac.get(
            posix_urljoin("/api/transformations/", str(get_uuid_from_seed("workflow 2"))),
        )

    assert put_response.status_code == 201

    put_response_json_without_io_ids = deepcopy(put_response.json())
    del put_response_json_without_io_ids["io_interface"]["inputs"][0]["id"]
    del put_response_json_without_io_ids["io_interface"]["outputs"][0]["id"]
    del put_response_json_without_io_ids["content"]["inputs"][0]["id"]
    del put_response_json_without_io_ids["content"]["outputs"][0]["id"]

    expected_put_response_json_without_io_ids = deepcopy(tr_json_workflow_2_added_io_for_operator)
    del expected_put_response_json_without_io_ids["io_interface"]["inputs"][0]["id"]
    del expected_put_response_json_without_io_ids["io_interface"]["outputs"][0]["id"]
    del expected_put_response_json_without_io_ids["content"]["inputs"][0]["id"]
    del expected_put_response_json_without_io_ids["content"]["outputs"][0]["id"]

    assert put_response_json_without_io_ids == expected_put_response_json_without_io_ids

    assert get_response.status_code == 200

    assert get_response.json() == put_response.json()


@pytest.mark.asyncio
async def test_update_transformation_revision_from_component_code(
    async_test_client, mocked_clean_test_db_session
):
    tr_json_component_2_draft = deepcopy(tr_json_component_2)
    tr_json_component_2_draft["state"] = "DRAFT"
    del tr_json_component_2_draft["released_timestamp"]

    tr_component_2 = TransformationRevision(**tr_json_component_2_draft)
    store_single_transformation_revision(tr_component_2)

    tr_json_component_2_draft["content"] = "{"
    tr_component_2_invalid_code = TransformationRevision(**tr_json_component_2_draft)
    tr_component_2_invalid_code.content = update_code(tr_component_2_invalid_code)

    tr_json_component_2_update_draft = deepcopy(tr_json_component_2_update)
    tr_json_component_2_update_draft["state"] = "DRAFT"
    del tr_json_component_2_update_draft["released_timestamp"]

    tr_component_2_update = TransformationRevision(**tr_json_component_2_update_draft)
    assert tr_component_2_update.content == 'code="code"'
    tr_component_2_update.content = update_code(tr_component_2_update)
    tr_component_2_update.content = expand_code(tr_component_2_update)

    assert '"category": "Test"' in tr_component_2_update.content

    async with async_test_client as ac:
        put_response_with_failure = await ac.put(
            "/api/transformations/",
            json=[tr_component_2_invalid_code.content],
        )
        put_response = await ac.put(
            "/api/transformations/",
            json=[tr_component_2_update.content],
        )
        get_response = await ac.get(
            posix_urljoin("/api/transformations/", str(get_uuid_from_seed("component 2"))),
        )

    assert put_response_with_failure.status_code == 207
    assert tr_component_2_invalid_code.content in put_response_with_failure.json()
    trafo_update_process_summary = put_response_with_failure.json()[
        tr_component_2_invalid_code.content
    ]
    assert trafo_update_process_summary["status"] == "FAILED"

    assert put_response.status_code == 207
    assert str(tr_component_2_update.id) in put_response.json()
    trafo_update_process_summary = put_response.json()[str(tr_component_2_update.id)]
    assert trafo_update_process_summary["status"] == "SUCCESS"

    assert get_response.status_code == 200
    assert get_response.json()["category"] == "Test"


@pytest.mark.asyncio
async def test_delete_transformation_revision_with_component(
    async_test_client, mocked_clean_test_db_session
):
    store_single_transformation_revision(
        TransformationRevision(**tr_json_component_2)  # RELEASED
    )
    store_single_transformation_revision(
        TransformationRevision(**tr_json_component_3)  # DRAFT
    )

    async with async_test_client as ac:
        response = await ac.delete(
            posix_urljoin("/api/transformations/", str(get_uuid_from_seed("component 1")))
        )
        assert response.status_code == 404

        response = await ac.delete(
            posix_urljoin("/api/transformations/", str(get_uuid_from_seed("component 2")))
        )
        assert response.status_code == 409

        response = await ac.delete(
            posix_urljoin("/api/transformations/", str(get_uuid_from_seed("component 2"))),
            params={"ignore_state": True},
        )
        assert response.status_code == 204
        tr_list = get_multiple_transformation_revisions(FilterParams(include_dependencies=False))
        assert len(tr_list) == 1  # component 3 is still stored in db

        response = await ac.delete(
            posix_urljoin("/api/transformations/", str(get_uuid_from_seed("component 3")))
        )
        assert response.status_code == 204
        tr_list = get_multiple_transformation_revisions(FilterParams(include_dependencies=False))
        assert len(tr_list) == 0


@pytest.mark.asyncio
async def test_publish_transformation_revision_with_component(
    async_test_client, mocked_clean_test_db_session
):
    store_single_transformation_revision(TransformationRevision(**tr_json_component_3))

    async with async_test_client as ac:
        response = await ac.put(
            posix_urljoin("/api/transformations/", str(get_uuid_from_seed("component 3"))),
            json=tr_json_component_3_publish,
        )

    assert response.status_code == 201
    assert response.json()["state"] == "RELEASED"
    assert "released_timestamp" in response.json()["content"]


@pytest.mark.asyncio
async def test_deprecate_transformation_revision_with_component(
    async_test_client, mocked_clean_test_db_session
):
    store_single_transformation_revision(TransformationRevision(**tr_json_component_2))

    async with async_test_client as ac:
        response = await ac.put(
            posix_urljoin("/api/transformations/", str(get_uuid_from_seed("component 2"))),
            json=tr_json_component_2_deprecate,
        )

    assert response.status_code == 201
    assert response.json()["name"] != "new name"
    assert response.json()["category"] != "Test"
    assert "disabled_timestamp" in response.json()["content"]
    assert "released_timestamp" in response.json()["content"]


@pytest.mark.asyncio
async def test_execute_for_transformation_revision(async_test_client, mocked_clean_test_db_session):
    tr_component_1 = TransformationRevision(**tr_json_component_1)
    tr_component_1.content = update_code(tr_component_1)
    store_single_transformation_revision(tr_component_1)
    tr_workflow_2 = TransformationRevision(**tr_json_workflow_2_update)

    store_single_transformation_revision(tr_workflow_2)

    update_or_create_nesting(tr_workflow_2)

    exec_by_id_input = ExecByIdInput(
        id=tr_workflow_2.id,
        wiring=tr_workflow_2.test_wiring,
        job_id=UUID("1270547c-b224-461d-9387-e9d9d465bbe1"),
    )

    async with async_test_client as ac:
        response = await ac.post(
            "/api/transformations/execute",
            json=json.loads(exec_by_id_input.json()),
        )

    assert response.status_code == 200
    resp_data = response.json()
    assert "output_types_by_output_name" in resp_data
    assert "job_id" in resp_data
    assert UUID(resp_data["job_id"]) == UUID("1270547c-b224-461d-9387-e9d9d465bbe1")


@pytest.mark.asyncio
async def test_execute_for_transformation_revision_with_missing_input_wiring(
    async_test_client, mocked_clean_test_db_session
):
    tr_component_1 = TransformationRevision(**tr_json_component_1)
    tr_component_1.content = update_code(tr_component_1)
    store_single_transformation_revision(tr_component_1)
    tr_workflow_2 = TransformationRevision(**tr_json_workflow_2_update)

    store_single_transformation_revision(tr_workflow_2)

    update_or_create_nesting(tr_workflow_2)

    wiring_with_missing_input = deepcopy(tr_workflow_2.test_wiring)
    wiring_with_missing_input.input_wirings.pop(0)

    exec_by_id_input = ExecByIdInput(
        id=tr_workflow_2.id,
        wiring=wiring_with_missing_input,
        job_id=UUID("1270547c-b224-461d-9387-e9d9d465bbe1"),
    )

    async with async_test_client as ac:
        response = await ac.post(
            "/api/transformations/execute",
            json=json.loads(exec_by_id_input.json()),
        )

    assert response.status_code == 422
    assert "Workflow Input 'wf_input' has no wiring!" in response.json()["detail"]


@pytest.mark.asyncio
async def test_execute_for_transformation_revision_without_job_id(
    async_test_client, mocked_clean_test_db_session
):
    tr_component_1 = TransformationRevision(**tr_json_component_1)
    tr_component_1.content = update_code(tr_component_1)
    store_single_transformation_revision(tr_component_1)
    tr_workflow_2 = TransformationRevision(**tr_json_workflow_2_update)

    store_single_transformation_revision(tr_workflow_2)

    update_or_create_nesting(tr_workflow_2)

    exec_by_id_input_json = {
        "id": str(tr_workflow_2.id),
        "wiring": json.loads(tr_workflow_2.test_wiring.json()),
    }

    assert hasattr(exec_by_id_input_json, "job_id") is False

    async with async_test_client as ac:
        response = await ac.post(
            "/api/transformations/execute",
            json=exec_by_id_input_json,
        )

    assert response.status_code == 200
    resp_data = response.json()
    assert "output_types_by_output_name" in resp_data
    assert "job_id" in resp_data


@pytest.mark.asyncio
async def test_execute_for_separate_runtime_container(
    async_test_client, mocked_clean_test_db_session
):
    with mock.patch(
        "hetdesrun.webservice.config.runtime_config",
        is_runtime_service=False,
    ):
        resp_mock = mock.Mock()
        resp_mock.status_code = 200
        resp_mock.json = mock.Mock(
            return_value={
                "output_results_by_output_name": {"wf_output": 100},
                "output_types_by_output_name": {"wf_output": "INT"},
                "result": "ok",
                "job_id": "1270547c-b224-461d-9387-e9d9d465bbe1",
            }
        )
        with mock.patch(
            "hetdesrun.backend.execution.httpx.AsyncClient.post",
            return_value=resp_mock,
        ) as mocked_post:
            tr_component_1 = TransformationRevision(**tr_json_component_1)
            tr_component_1.content = update_code(tr_component_1)
            store_single_transformation_revision(tr_component_1)
            tr_workflow_2 = TransformationRevision(**tr_json_workflow_2_update)

            store_single_transformation_revision(tr_workflow_2)

            update_or_create_nesting(tr_workflow_2)

            exec_by_id_input = ExecByIdInput(
                id=tr_workflow_2.id,
                wiring=tr_workflow_2.test_wiring,
                job_id=UUID("1270547c-b224-461d-9387-e9d9d465bbe1"),
            )

            async with async_test_client as ac:
                response = await ac.post(
                    "/api/transformations/execute",
                    json=json.loads(exec_by_id_input.json()),
                )

            assert response.status_code == 200
            resp_data = response.json()
            assert "output_types_by_output_name" in resp_data
            assert "job_id" in resp_data
            assert UUID(resp_data["job_id"]) == UUID("1270547c-b224-461d-9387-e9d9d465bbe1")
            mocked_post.assert_called_once()


@pytest.mark.asyncio
async def test_execute_for_transformation_revision_component_with_optional_inputs(
    async_test_client, mocked_clean_test_db_session
):
    path = "tests/data/components/test_optional_default_params.json"
    tr_json = load_json(path)
    tr = TransformationRevision(**tr_json)
    store_single_transformation_revision(tr)

    exec_by_id_input_json = {
        "id": tr_json["id"],
        "wiring": tr_json["test_wiring"],
    }

    async with async_test_client as ac:
        response = await ac.post(
            "/api/transformations/execute",
            json=exec_by_id_input_json,
        )

    assert response.status_code == 200
    response_json = response.json()
    # The component is designed to raise an error with the provided error message
    assert "traceback" in response_json
    assert tr_json["io_interface"]["inputs"][0]["value"] in response_json["traceback"]


@pytest.mark.asyncio
async def test_execute_for_transformation_revision_workflow_with_optional_inputs(
    async_test_client, mocked_clean_test_db_session
):
    component_path = "tests/data/components/test_optional_default_params.json"
    component_tr_json = load_json(component_path)
    component_tr = TransformationRevision(**component_tr_json)
    store_single_transformation_revision(component_tr)

    workflow_path = "tests/data/workflows/test_optional_default_params.json"
    workflow_tr_json = load_json(workflow_path)
    workflow_tr = TransformationRevision(**workflow_tr_json)
    store_single_transformation_revision(workflow_tr)

    exec_by_id_input_json = {
        "id": workflow_tr_json["id"],
        "wiring": workflow_tr_json["test_wiring"],
    }

    async with async_test_client as ac:
        response = await ac.post(
            "/api/transformations/execute",
            json=exec_by_id_input_json,
        )

    assert response.status_code == 200
    response_json = response.json()
    # The component is designed to raise an error with the provided error message
    assert "traceback" in response_json
    assert workflow_tr_json["io_interface"]["inputs"][2]["value"] in response_json["traceback"]


@pytest.mark.asyncio
async def test_execute_asynchron_for_transformation_revision_works(
    async_test_client, mocked_clean_test_db_session
):
    tr_component_1 = TransformationRevision(**tr_json_component_1)
    tr_component_1.content = update_code(tr_component_1)
    store_single_transformation_revision(tr_component_1)
    tr_workflow_2 = TransformationRevision(**tr_json_workflow_2_update)

    store_single_transformation_revision(tr_workflow_2)

    update_or_create_nesting(tr_workflow_2)

    exec_by_id_input = ExecByIdInput(
        id=tr_workflow_2.id,
        wiring=tr_workflow_2.test_wiring,
        job_id=UUID("1270547c-b224-461d-9387-e9d9d465bbe1"),
    )

    send_mock = mock.AsyncMock()
    with mock.patch(
        "hetdesrun.backend.service.transformation_router.send_result_to_callback_url",
        new=send_mock,
    ):
        async with async_test_client as ac:
            response = await ac.post(
                "/api/transformations/execute-async",
                json=json.loads(exec_by_id_input.json()),
                params={"callback_url": "http://callback-url.com/"},
            )

        assert response.status_code == 202
        assert "message" in response.json()
        assert "1270547c-b224-461d-9387-e9d9d465bbe1" in response.json()["message"]
        assert send_mock.called
        func_name, args, kwargs = send_mock.mock_calls[0]
        assert func_name == ""
        assert len(kwargs) == 0
        assert len(args) == 2
        assert args[0] == "http://callback-url.com/"
        assert args[1].job_id == UUID("1270547c-b224-461d-9387-e9d9d465bbe1")
        assert args[1].output_results_by_output_name == {"wf_output": 100}
        assert args[1].output_types_by_output_name == {"wf_output": "INT"}
        assert str(args[1].result) == "ok"


@pytest.mark.asyncio
async def test_execute_async_for_transformation_revision_with_exception(
    async_test_client, mocked_clean_test_db_session, caplog
):
    tr_workflow_2 = TransformationRevision(**tr_json_workflow_2_update)

    exec_by_id_input = ExecByIdInput(
        id=tr_workflow_2.id,
        wiring=tr_workflow_2.test_wiring,
        job_id=UUID("1270547c-b224-461d-9387-e9d9d465bbe1"),
    )
    async with async_test_client as ac:
        with caplog.at_level(logging.ERROR):
            with mock.patch(
                "hetdesrun.backend.service.transformation_router."
                "handle_trafo_revision_execution_request",
                side_effect=HTTPException(404),
            ):
                await ac.post(
                    "/api/transformations/execute-async",
                    json=json.loads(exec_by_id_input.json()),
                    params={"callback_url": "http://callback-url.com"},
                )

                assert "1270547c-b224-461d-9387-e9d9d465bbe1" in caplog.text
                assert "background task" in caplog.text
                assert "Not Found" in caplog.text

            caplog.clear()
            with mock.patch(
                "hetdesrun.backend.service.transformation_router."
                "handle_trafo_revision_execution_request",
                side_effect=Exception,
            ):
                with pytest.raises(Exception):  # noqa: PT011,B017
                    await ac.post(
                        "/api/transformations/execute-async",
                        json=json.loads(exec_by_id_input.json()),
                        params={"callback_url": "http://callback-url.com"},
                    )

                assert "1270547c-b224-461d-9387-e9d9d465bbe1" in caplog.text
                assert "background task" in caplog.text
                assert "unexpected error" in caplog.text


@pytest.mark.asyncio
async def test_execute_latest_for_transformation_revision_works(
    async_test_client, mocked_clean_test_db_session
):
    tr_component_1 = TransformationRevision(**tr_json_component_1)
    tr_component_1.content = update_code(tr_component_1)
    store_single_transformation_revision(tr_component_1)

    tr_component_1_new_revision = TransformationRevision(**tr_json_component_1_new_revision)
    tr_component_1_new_revision.content = update_code(tr_component_1_new_revision)
    tr_component_1_new_revision.release()
    store_single_transformation_revision(tr_component_1_new_revision)

    exec_latest_by_group_id_input = ExecLatestByGroupIdInput(
        revision_group_id=tr_component_1.revision_group_id,
        wiring=tr_component_1.test_wiring,
        job_id=UUID("1270547c-b224-461d-9387-e9d9d465bbe1"),
    )

    async with async_test_client as ac:
        response = await ac.post(
            "/api/transformations/execute-latest",
            json=json.loads(exec_latest_by_group_id_input.json()),
        )

    assert response.status_code == 200
    resp_data = response.json()
    assert "output_types_by_output_name" in resp_data
    assert resp_data["output_types_by_output_name"]["operator_output"] == "STRING"
    assert "job_id" in resp_data
    assert UUID(resp_data["job_id"]) == UUID("1270547c-b224-461d-9387-e9d9d465bbe1")


@pytest.mark.asyncio
async def test_execute_latest_for_transformation_revision_no_revision_in_db(
    async_test_client, mocked_clean_test_db_session
):
    tr_component_1 = TransformationRevision(**tr_json_component_1)
    tr_component_1.content = update_code(tr_component_1)

    exec_latest_by_group_id_input = ExecLatestByGroupIdInput(
        revision_group_id=tr_component_1.revision_group_id,
        wiring=tr_component_1.test_wiring,
    )

    async with async_test_client as ac:
        response = await ac.post(
            "/api/transformations/execute-latest",
            json=json.loads(exec_latest_by_group_id_input.json()),
        )

    assert response.status_code == 404
    assert (
        "no released transformation revisions with revision group id" in response.json()["detail"]
    )


@pytest.mark.asyncio
async def test_execute_latest_async_for_transformation_revision_works(
    async_test_client, mocked_clean_test_db_session
):
    tr_component_1 = TransformationRevision(**tr_json_component_1)
    tr_component_1.content = update_code(tr_component_1)
    store_single_transformation_revision(tr_component_1)

    tr_component_1_new_revision = TransformationRevision(**tr_json_component_1_new_revision)
    tr_component_1_new_revision.content = update_code(tr_component_1_new_revision)
    tr_component_1_new_revision.release()
    store_single_transformation_revision(tr_component_1_new_revision)

    exec_latest_by_group_id_input = ExecLatestByGroupIdInput(
        revision_group_id=tr_component_1.revision_group_id,
        wiring=tr_component_1.test_wiring,
        job_id=UUID("1270547c-b224-461d-9387-e9d9d465bbe1"),
    )

    send_mock = mock.AsyncMock()
    with mock.patch(
        "hetdesrun.backend.service.transformation_router.send_result_to_callback_url",
        new=send_mock,
    ):
        async with async_test_client as ac:
            response = await ac.post(
                "/api/transformations/execute-latest-async",
                json=json.loads(exec_latest_by_group_id_input.json()),
                params={"callback_url": "http://callback-url.com/"},
            )

        assert response.status_code == 202
        assert "message" in response.json()
        assert "1270547c-b224-461d-9387-e9d9d465bbe1" in response.json()["message"]
        assert send_mock.called
        func_name, args, kwargs = send_mock.mock_calls[0]
        assert func_name == ""
        assert len(kwargs) == 0
        assert len(args) == 2
        assert args[0] == "http://callback-url.com/"

        assert args[1].job_id == UUID("1270547c-b224-461d-9387-e9d9d465bbe1")
        assert args[1].output_results_by_output_name == {"operator_output": 100}
        assert args[1].output_types_by_output_name == {"operator_output": "STRING"}
        assert str(args[1].result) == "ok"


@pytest.mark.asyncio
async def test_execute_latest_async_for_transformation_revision_with_exception(
    async_test_client, mocked_clean_test_db_session, caplog
):
    tr_component_1 = TransformationRevision(**tr_json_component_1)

    exec_latest_by_group_id_input = ExecLatestByGroupIdInput(
        revision_group_id=tr_component_1.revision_group_id,
        wiring=tr_component_1.test_wiring,
        job_id=UUID("1270547c-b224-461d-9387-e9d9d465bbe1"),
    )
    async with async_test_client as ac:
        with caplog.at_level(logging.ERROR):
            with mock.patch(
                "hetdesrun.backend.service.transformation_router."
                "handle_latest_trafo_revision_execution_request",
                side_effect=HTTPException(404),
            ):
                await ac.post(
                    "/api/transformations/execute-latest-async",
                    json=json.loads(exec_latest_by_group_id_input.json()),
                    params={"callback_url": "http://callback-url.com"},
                )

                assert "1270547c-b224-461d-9387-e9d9d465bbe1" in caplog.text
                assert "background task" in caplog.text
                assert "Not Found" in caplog.text

            caplog.clear()
            with mock.patch(
                "hetdesrun.backend.service.transformation_router."
                "handle_latest_trafo_revision_execution_request",
                side_effect=Exception,
            ):
                with pytest.raises(Exception):  # noqa: PT011,B017
                    await ac.post(
                        "/api/transformations/execute-latest-async",
                        json=json.loads(exec_latest_by_group_id_input.json()),
                        params={"callback_url": "http://callback-url.com"},
                    )

                assert "1270547c-b224-461d-9387-e9d9d465bbe1" in caplog.text
                assert "background task" in caplog.text
                assert "unexpected error" in caplog.text


@pytest.mark.asyncio
async def test_execute_for_nested_workflow(async_test_client, mocked_clean_test_db_session):
    async with async_test_client as ac:
        json_files = [
            "./transformations/components/connectors/pass-through-integer_100_57eea09f-d28e-89af-4e81-2027697a3f0f.json",
            "./transformations/components/connectors/pass-through-series_100_bfa27afc-dea8-b8aa-4b15-94402f0739b6.json",
            "./transformations/components/connectors/pass-through-string_100_2b1b474f-ddf5-1f4d-fec4-17ef9122112b.json",
            "./transformations/components/remaining-useful-life/univariate-linear-rul-regression_100_8d61a267-3a71-51cd-2817-48c320469d6b.json",
            "./transformations/components/visualization/univariate-linear-rul-regression-result-plot_100_9c3f88ce-1311-241e-18b7-acf7d3f5a051.json",
            "./transformations/components/arithmetic/consecutive-differences_100_ce801dcb-8ce1-14ad-029d-a14796dcac92.json",
            "./transformations/components/basic/filter_100_18260aab-bdd6-af5c-cac1-7bafde85188f.json",
            "./transformations/components/basic/greater-or-equal_100_f759e4c0-1468-0f2e-9740-41302b860193.json",
            "./transformations/components/basic/last-datetime-index_100_c8e3bc64-b214-6486-31db-92a8888d8991.json",
            "./transformations/components/basic/restrict-to-time-interval_100_bf469c0a-d17c-ca6f-59ac-9838b2ff67ac.json",
            "./transformations/components/connectors/pass-through-float_100_2f511674-f766-748d-2de3-ad5e62e10a1a.json",
            "./transformations/components/visualization/single-timeseries-plot_100_8fba9b51-a0f1-6c6c-a6d4-e224103b819c.json",
            "./transformations/workflows/examples/data-from-last-positive-step_100_2cbb87e7-ea99-4404-abe1-be550f22763f.json",
            "./transformations/workflows/examples/univariate-linear-rul-regression-example_100_806df1b9-2fc8-4463-943f-3d258c569663.json",
            "./transformations/workflows/examples/linear-rul-from-last-positive-step_100_3d504361-e351-4d52-8734-391aa47e8f24.json",
        ]

        for file in json_files:
            tr_json = load_json(file)

            response = await ac.put(
                posix_urljoin(
                    get_config().hd_backend_api_url,
                    "transformations",
                    tr_json["id"],
                ),
                params={"allow_overwrite_released": True},
                json=tr_json,
            )

        component_id = UUID("57eea09f-d28e-89af-4e81-2027697a3f0f")
        updated_component = read_single_transformation_revision(component_id)
        updated_component.deprecate()

        response = await ac.put(
            "/api/transformations/" + str(component_id),
            json=json.loads(updated_component.json(by_alias=True)),
        )

        # linear rul from last positive step
        workflow_id = UUID("3d504361-e351-4d52-8734-391aa47e8f24")
        tr_workflow = read_single_transformation_revision(workflow_id)

        exec_by_id_input = ExecByIdInput(id=workflow_id, wiring=tr_workflow.test_wiring)

        response = await ac.post(
            "/api/transformations/execute",
            json=json.loads(exec_by_id_input.json()),
        )

        assert response.status_code == 200
        assert "output_types_by_output_name" in response.json()
        assert response.json()["result"] == "ok"
        assert abs(response.json()["output_results_by_output_name"]["intercept"] - 2.88) < 0.01
        assert response.json()["output_results_by_output_name"]["before_step_detect"] == {}
        assert response.json()["output_results_by_output_name"]["rul_regression_result_plot"] == {}


@pytest.mark.asyncio
async def test_execute_for_transformation_revision_with_nan_and_nat_input(
    async_test_client, mocked_clean_test_db_session
):
    async with async_test_client as ac:
        json_files = [
            "./transformations/components/connectors/pass-through_100_1946d5f8-44a8-724c-176f-16f3e49963af.json",
            "./transformations/components/connectors/pass-through-series_100_bfa27afc-dea8-b8aa-4b15-94402f0739b6.json",
        ]

        for file in json_files:
            tr_json = load_json(file)

            response_nan = await ac.put(
                posix_urljoin(
                    get_config().hd_backend_api_url,
                    "transformations",
                    tr_json["id"],
                ),
                params={"allow_overwrite_released": True},
                json=tr_json,
            )

        tr_id_any = UUID("1946d5f8-44a8-724c-176f-16f3e49963af")
        tr_id_series = UUID("bfa27afc-dea8-b8aa-4b15-94402f0739b6")
        wiring_nan = WorkflowWiring(
            input_wirings=[
                InputWiring(
                    adapter_id="direct_provisioning",
                    workflow_input_name="input",
                    filters={"value": '{"0":1.2,"1":null, "2":5}'},
                ),
            ],
            output_wirings=[],
        )
        wiring_nat = WorkflowWiring(
            input_wirings=[
                InputWiring(
                    adapter_id="direct_provisioning",
                    workflow_input_name="input",
                    filters={
                        "value": '{"2020-05-01T00:00:00.000Z": "2020-05-01T01:00:00.000Z", "2020-05-01T02:00:00.000Z": null}'  # noqa: E501
                    },
                ),
            ],
            output_wirings=[],
        )
        exec_by_id_input_nan = ExecByIdInput(id=tr_id_any, wiring=wiring_nan)
        exec_by_id_input_nat = ExecByIdInput(id=tr_id_series, wiring=wiring_nat)
        response_nan = await ac.post(
            "/api/transformations/execute",
            json=json.loads(exec_by_id_input_nan.json()),
        )

        assert response_nan.status_code == 200
        assert "output_results_by_output_name" in response_nan.json()
        output_results_by_output_name = response_nan.json()["output_results_by_output_name"]
        assert "output" in output_results_by_output_name
        assert len(output_results_by_output_name["output"]) == 3
        assert output_results_by_output_name["output"]["1"] == None  # noqa: E711

        response_nat = await ac.post(
            "/api/transformations/execute",
            json=json.loads(exec_by_id_input_nat.json()),
        )

        assert response_nat.status_code == 200
        assert "output_results_by_output_name" in response_nat.json()
        output_results_by_output_name = response_nat.json()["output_results_by_output_name"]
        assert "output" in output_results_by_output_name
        assert len(output_results_by_output_name["output"]["__data__"]) == 3  # split format
        assert (
            output_results_by_output_name["output"]["__data__"]["data"][1] == None  # noqa: E711
        )

        tr_group_id_any = UUID("1946d5f8-44a8-724c-176f-16f3e49963af")
        tr_group_id_series = UUID("bfa27afc-dea8-b8aa-4b15-94402f0739b6")
        exec_latest_by_group_id_input_nan = ExecLatestByGroupIdInput(
            revision_group_id=tr_group_id_any, wiring=wiring_nan
        )
        exec_latest_by_group_id_input_nat = ExecLatestByGroupIdInput(
            revision_group_id=tr_group_id_series, wiring=wiring_nat
        )
        response_latest_nan = await ac.post(
            "/api/transformations/execute-latest",
            json=json.loads(exec_latest_by_group_id_input_nan.json()),
        )

        assert response_latest_nan.status_code == 200
        assert "output_results_by_output_name" in response_latest_nan.json()
        output_results_by_output_name = response_latest_nan.json()["output_results_by_output_name"]
        assert "output" in output_results_by_output_name
        assert len(output_results_by_output_name["output"]) == 3
        assert output_results_by_output_name["output"]["1"] == None  # noqa: E711

        response_latest_nat = await ac.post(
            "/api/transformations/execute-latest",
            json=json.loads(exec_latest_by_group_id_input_nat.json()),
        )

        assert response_latest_nat.status_code == 200
        assert "output_results_by_output_name" in response_latest_nat.json()
        output_results_by_output_name = response_latest_nat.json()["output_results_by_output_name"]
        assert "output" in output_results_by_output_name
        assert len(output_results_by_output_name["output"]["__data__"]) == 3
        assert (
            output_results_by_output_name["output"]["__data__"]["data"][1] == None  # noqa: E711
        )


@pytest.mark.asyncio
async def test_put_workflow_transformation(async_test_client, mocked_clean_test_db_session):
    json_files = [
        "./transformations/components/connectors/pass-through-series_100_bfa27afc-dea8-b8aa-4b15-94402f0739b6.json",
        "./transformations/components/arithmetic/consecutive-differences_100_ce801dcb-8ce1-14ad-029d-a14796dcac92.json",
        "./transformations/components/basic/filter_100_18260aab-bdd6-af5c-cac1-7bafde85188f.json",
        "./transformations/components/basic/greater-or-equal_100_f759e4c0-1468-0f2e-9740-41302b860193.json",
        "./transformations/components/basic/last-datetime-index_100_c8e3bc64-b214-6486-31db-92a8888d8991.json",
        "./transformations/components/basic/restrict-to-time-interval_100_bf469c0a-d17c-ca6f-59ac-9838b2ff67ac.json",
        "./transformations/components/connectors/pass-through-float_100_2f511674-f766-748d-2de3-ad5e62e10a1a.json",
    ]

    for file in json_files:
        tr_json = load_json(file)
        store_single_transformation_revision(TransformationRevision(**tr_json))

    example_workflow_tr_json = load_json(
        "./transformations/workflows/examples/data-from-last-positive-step_100_2cbb87e7-ea99-4404-abe1-be550f22763f.json"
    )

    async with async_test_client as ac:
        response = await ac.put(
            posix_urljoin("/api/transformations/", example_workflow_tr_json["id"]),
            json=example_workflow_tr_json,
        )

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_put_component_transformation_with_update_code(
    async_test_client, mocked_clean_test_db_session
):
    path = "./tests/data/components/alerts-from-score_100_38f168ef-cb06-d89c-79b3-0cd823f32e9d.json"  # noqa: E501
    example_component_tr_json = load_json(path)

    async with async_test_client as ac:
        response = await ac.put(
            posix_urljoin("/api/transformations/", example_component_tr_json["id"]),
            params={"update_component_code": True},
            json=example_component_tr_json,
        )

    component_tr_in_db = read_single_transformation_revision(example_component_tr_json["id"])

    assert response.status_code == 201
    assert "COMPONENT_INFO" in response.json()["content"]
    assert "COMPONENT_INFO" in component_tr_in_db.content
    assert "register" not in response.json()["content"]
    assert "register" not in component_tr_in_db.content


@pytest.mark.asyncio
async def test_put_component_transformation_without_update_code(
    async_test_client, mocked_clean_test_db_session
):
    path = "./tests/data/components/alerts-from-score_100_38f168ef-cb06-d89c-79b3-0cd823f32e9d.json"  # noqa: E501
    example_component_tr_json = load_json(path)

    async with async_test_client as ac:
        response = await ac.put(
            posix_urljoin("/api/transformations/", example_component_tr_json["id"]),
            params={"update_component_code": False},
            json=example_component_tr_json,
        )

    component_tr_in_db = read_single_transformation_revision(example_component_tr_json["id"])

    assert response.status_code == 201
    assert "COMPONENT_INFO" not in response.json()["content"]
    assert "COMPONENT_INFO" not in component_tr_in_db.content
    assert "register" in response.json()["content"]
    assert "register" in component_tr_in_db.content


@pytest.mark.asyncio
async def test_put_multiple_trafos(async_test_client, mocked_clean_test_db_session):
    path = "./tests/data/components/alerts-from-score_100_38f168ef-cb06-d89c-79b3-0cd823f32e9d.json"  # noqa: E501
    example_component_tr_json = load_json(path)

    async with async_test_client as ac:
        response = await ac.put(
            "/api/transformations/",
            params={"update_component_code": False},
            json=[example_component_tr_json],
        )

        assert response.status_code == 207

        success_info = response.json()
        assert len(success_info) == 1
        assert list(success_info.values())[0]["status"] == "SUCCESS"


@pytest.mark.asyncio
async def test_put_releasing_drafts(async_test_client, mocked_clean_test_db_session):
    """Test the release_drafts query param of the multiple put endpoint"""
    path = "./tests/data/components/alerts-from-score_100_38f168ef-cb06-d89c-79b3-0cd823f32e9d.json"  # noqa: E501
    example_component_tr_json = load_json(path)

    example_component_tr_json.pop("released_timestamp")
    example_component_tr_json["state"] = "DRAFT"

    trafo = TransformationRevision(**example_component_tr_json)

    async with async_test_client as ac:
        response = await ac.put(
            "/api/transformations/",
            params={"update_component_code": False, "release_drafts": True},
            json=[json.loads(trafo.json())],
        )

        assert response.status_code == 207

        success_info = response.json()
        assert len(success_info) == 1
        assert list(success_info.values())[0]["status"] == "SUCCESS"

        response = await ac.get(f"/api/transformations/{str(trafo.id)}")
        assert response.status_code == 200
        trafo_from_resp = TransformationRevision(**response.json())

        assert trafo_from_resp.state is State.RELEASED
