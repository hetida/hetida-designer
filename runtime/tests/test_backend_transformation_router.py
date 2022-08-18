import json
from copy import deepcopy
from posixpath import join as posix_urljoin
from unittest import mock
from uuid import UUID

import pytest
from starlette.testclient import TestClient

from hetdesrun.backend.execution import ExecByIdInput, ExecLatestByGroupIdInput
from hetdesrun.component.code import update_code
from hetdesrun.exportimport.importing import load_json
from hetdesrun.persistence import get_db_engine, sessionmaker
from hetdesrun.persistence.dbmodels import Base
from hetdesrun.persistence.dbservice.nesting import update_or_create_nesting
from hetdesrun.persistence.dbservice.revision import (
    read_single_transformation_revision,
    store_single_transformation_revision,
)
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.utils import get_uuid_from_seed
from hetdesrun.webservice.config import get_config, runtime_config


@pytest.fixture(scope="function")
def clean_test_db_engine(use_in_memory_db):
    if use_in_memory_db:
        in_memory_database_url = "sqlite+pysqlite:///:memory:"
        engine = get_db_engine(override_db_url=in_memory_database_url)
    else:
        engine = get_db_engine()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    return engine


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
    "content": 'from hetdesrun.component.registration import register\nfrom hetdesrun.datatypes import DataType\n\n# ***** DO NOT EDIT LINES BELOW *****\n# These lines may be overwritten if component details or inputs/outputs change.\n@register(\n    inputs={"operator_input": DataType.Integer},\n    outputs={"operator_output": DataType.Integer},\n    component_name="Pass Through Integer",\n    description="Just outputs its input value",\n    category="Connectors",\n    uuid="57eea09f-d28e-89af-4e81-2027697a3f0f",\n    group_id="57eea09f-d28e-89af-4e81-2027697a3f0f",\n    tag="1.0.0"\n)\ndef main(*, input):\n    # entrypoint function for this component\n    # ***** DO NOT EDIT LINES ABOVE *****\n    # write your function code here.\n\n    return {"operator_output": operator_input}\n',
    "test_wiring": {
        "input_wirings": [
            {
                "workflow_input_name": "operator_input",
                "adapter_id": "direct_provisioning",
                "filters": {"value": 100},
            },
        ],
        "output_wirings": [
            {
                "workflow_output_name": "operator_output",
                "adapter_id": "direct_provisioning",
            },
        ],
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
    "content": "code",
    "test_wiring": {
        "input_wirings": [
            {
                "workflow_input_name": "operator_input",
                "adapter_id": "direct_provisioning",
                "filters": {"value": 100},
            },
        ],
        "output_wirings": [
            {
                "workflow_output_name": "operator_output",
                "adapter_id": "direct_provisioning",
            },
        ],
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
    "content": "code",
    "test_wiring": {
        "input_wirings": [],
        "output_wirings": [],
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
    "content": "code",
    "test_wiring": {
        "input_wirings": [],
        "output_wirings": [],
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
    "content": "code",
    "test_wiring": {
        "input_wirings": [],
        "output_wirings": [],
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
    "documentation": "# New Component/Workflow\n## Description\n## Inputs\n## Outputs\n## Details\n## Examples\n",
    "content": '# add your own imports here, e.g.\n# import pandas as pd\n# import numpy as np\n\n\n# ***** DO NOT EDIT LINES BELOW *****\n# These lines may be overwritten if component details or inputs/outputs change.\nCOMPONENT_INFO = {\n    "inputs": {\n        "new_input_1": "STRING",\n    },\n    "outputs": {\n        "new_output_1": "BOOLEAN",\n    },\n    "name": "Test1",\n    "category": "Äpfel",\n    "description": "New created component test",\n    "version_tag": "1.0.1",\n    "id": "977cbb10-ca82-4893-b062-6036f918344d",\n    "revision_group_id": "a7128772-9729-4519-bc55-540327641a0c",\n    "state": "DRAFT",\n}\n\n\ndef main(*, new_input_1):\n    # entrypoint function for this component\n    # ***** DO NOT EDIT LINES ABOVE *****\n    # write your function code here.\n    print "test"\n    pass',
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
    "test_wiring": {"input_wirings": [], "output_wirings": []},
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
    "documentation": "# New Component/Workflow\n## Description\n## Inputs\n## Outputs\n## Details\n## Examples\n",
    "content": '# add your own imports here, e.g.\n# import pandas as pd\n# import numpy as np\n\n\n# ***** DO NOT EDIT LINES BELOW *****\n# These lines may be overwritten if component details or inputs/outputs change.\nCOMPONENT_INFO = {\n    "inputs": {\n        "new_input_1": "STRING",\n    },\n    "outputs": {\n        "new_output_1": "BOOLEAN",\n    },\n    "name": "Test1",\n    "category": "Äpfel",\n    "description": "New created component test",\n    "version_tag": "1.0.1",\n    "id": "977cbb10-ca82-4893-b062-6036f918344d",\n    "revision_group_id": "a7128772-9729-4519-bc55-540327641a0c",\n    "state": "DRAFT",\n}\n\n\ndef main(*, new_input_1):\n    # entrypoint function for this component\n    # ***** DO NOT EDIT LINES ABOVE *****\n    # write your function code here.\n    print "test"\n    pass',
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
    "test_wiring": {"input_wirings": [], "output_wirings": []},
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
    },
}

tr_json_workflow_2 = {
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
    },
    "test_wiring": {
        "input_wirings": [
            {
                "workflow_input_name": "wf_input",
                "adapter_id": "direct_provisioning",
                "filters": {"value": 100},
            },
        ],
        "output_wirings": [
            {
                "workflow_output_name": "wf_output",
                "adapter_id": "direct_provisioning",
            },
        ],
    },
}
tr_json_workflow_2_update = deepcopy(tr_json_workflow_2)
tr_json_workflow_2_update["name"] = "new name"


@pytest.mark.asyncio
async def test_get_all_transformation_revisions_with_valid_db_entries(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        store_single_transformation_revision(
            TransformationRevision(**tr_json_component_1)
        )
        store_single_transformation_revision(
            TransformationRevision(**tr_json_component_2)
        )
        store_single_transformation_revision(
            TransformationRevision(**tr_json_workflow_1)
        )
        store_single_transformation_revision(
            TransformationRevision(**tr_json_workflow_2)
        )
        async with async_test_client as ac:
            response = await ac.get("/api/transformations/")

        assert response.status_code == 200
        assert response.json()[0] == tr_json_component_1
        assert response.json()[1] == tr_json_component_2
        assert response.json()[2] == tr_json_workflow_1
        assert response.json()[3] == tr_json_workflow_2


@pytest.mark.asyncio
async def test_get_all_transformation_revisions_with_no_db_entries(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        async with async_test_client as ac:
            response = await ac.get("/api/transformations/")

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_all_transformation_revisions_with_specified_state(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
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
        tr_workflow_2 = TransformationRevision(**tr_json_workflow_2)
        tr_workflow_2.deprecate()
        store_single_transformation_revision(tr_workflow_2)
        async with async_test_client as ac:
            response_draft = await ac.get("/api/transformations/?state=DRAFT")
            response_released = await ac.get("/api/transformations/?state=RELEASED")
            response_disabled = await ac.get("/api/transformations/?state=DISABLED")
            response_foo = await ac.get("/api/transformations/?state=foo")

        assert response_draft.status_code == 200
        assert len(response_draft.json()) == 2
        assert response_draft.json()[0] == tr_json_component_1
        assert response_draft.json()[1] == tr_json_workflow_1
        assert response_released.status_code == 200
        assert len(response_released.json()) == 1
        assert response_released.json()[0] == tr_json_component_2
        assert response_disabled.status_code == 200
        assert len(response_disabled.json()) == 1
        assert response_disabled.json()[0]["id"] == tr_json_workflow_2["id"]
        assert response_disabled.json()[0]["state"] == "DISABLED"
        assert response_foo.status_code == 422
        assert (
            "not a valid enumeration member" in response_foo.json()["detail"][0]["msg"]
        )


@pytest.mark.asyncio
async def test_get_all_transformation_revisions_with_specified_type(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
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
            TransformationRevision(**tr_json_workflow_2)  # DRAFT
        )

        async with async_test_client as ac:
            response_component = await ac.get("/api/transformations/?type=COMPONENT")
            response_workflow = await ac.get("/api/transformations/?type=WORKFLOW")
            response_foo = await ac.get("/api/transformations/?type=foo")

        assert response_component.status_code == 200
        assert len(response_component.json()) == 2
        assert response_component.json()[0] == tr_json_component_1
        assert response_component.json()[1] == tr_json_component_2
        assert response_workflow.status_code == 200
        assert len(response_workflow.json()) == 2
        assert response_workflow.json()[0] == tr_json_workflow_1
        assert response_workflow.json()[1] == tr_json_workflow_2
        assert response_foo.status_code == 422
        assert (
            "not a valid enumeration member" in response_foo.json()["detail"][0]["msg"]
        )


@pytest.mark.asyncio
async def test_get_all_transformation_revisions_with_specified_type_and_state(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
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
            TransformationRevision(**tr_json_workflow_2)  # DRAFT
        )

        async with async_test_client as ac:
            response_released_component = await ac.get(
                "/api/transformations/?type=COMPONENT&state=RELEASED"
            )
            response_draft_workflow = await ac.get(
                "/api/transformations/?type=WORKFLOW&state=DRAFT"
            )

        assert response_released_component.status_code == 200
        assert len(response_released_component.json()) == 1
        assert response_released_component.json()[0] == tr_json_component_2
        assert response_draft_workflow.status_code == 200
        assert len(response_draft_workflow.json()) == 2
        assert response_draft_workflow.json()[0] == tr_json_workflow_1
        assert response_draft_workflow.json()[1] == tr_json_workflow_2


@pytest.mark.asyncio
async def test_get_transformation_revision_by_id_with_component(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        store_single_transformation_revision(
            TransformationRevision(**tr_json_component_1)
        )

        async with async_test_client as ac:
            response = await ac.get(
                posix_urljoin(
                    "/api/transformations/", str(get_uuid_from_seed("component 1"))
                )
            )
        assert response.status_code == 200
        assert response.json() == tr_json_component_1


@pytest.mark.asyncio
async def test_get_transformation_revision_by_id_with_inexistent_component(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
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
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        store_single_transformation_revision(
            TransformationRevision(**tr_json_workflow_1)
        )

        async with async_test_client as ac:
            response = await ac.get(
                posix_urljoin(
                    "/api/transformations/", str(get_uuid_from_seed("workflow 1"))
                )
            )
        assert response.status_code == 200
        assert response.json() == tr_json_workflow_1


@pytest.mark.asyncio
async def test_get_transformation_revision_by_id_with_inexistent_workflow(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
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
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):

        async with async_test_client as ac:
            response = await ac.post("/api/transformations/", json=tr_json_workflow_2)

        assert response.status_code == 201
        assert response.json()["name"] == tr_json_workflow_2["name"]


@pytest.mark.asyncio
async def test_update_transformation_revision_with_workflow(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        store_single_transformation_revision(
            TransformationRevision(**tr_json_workflow_2)
        )

        async with async_test_client as ac:
            response = await ac.put(
                posix_urljoin(
                    "/api/transformations/", str(get_uuid_from_seed("workflow 2"))
                ),
                json=tr_json_workflow_2_update,
            )

        workflow_tr_in_db = read_single_transformation_revision(
            get_uuid_from_seed("workflow 2")
        )

        assert response.status_code == 201
        assert response.json()["name"] == "new name"
        assert len(workflow_tr_in_db.content.links) == 2


@pytest.mark.asyncio
async def test_update_transformation_revision_with_invalid_name_workflow(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        store_single_transformation_revision(
            TransformationRevision(**tr_json_workflow_2)
        )

        tr_json_workflow_2_update_invalid_name = deepcopy(tr_json_workflow_2_update)
        tr_json_workflow_2_update_invalid_name["name"] = "'"

        async with async_test_client as ac:
            response = await ac.put(
                posix_urljoin(
                    "/api/transformations/", str(get_uuid_from_seed("workflow 2"))
                ),
                json=tr_json_workflow_2_update_invalid_name,
            )

        print(response.json())
        assert response.status_code == 422
        assert "string does not match regex" in response.json()["detail"][0]["msg"]
        assert "name" in response.json()["detail"][0]["loc"]


@pytest.mark.asyncio
async def test_update_transformation_revision_with_non_existing_workflow(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        async with async_test_client as ac:
            response = await ac.put(
                posix_urljoin(
                    "/api/transformations/", str(get_uuid_from_seed("workflow 2"))
                ),
                json=tr_json_workflow_2_update,
            )

        workflow_tr_in_db = read_single_transformation_revision(
            get_uuid_from_seed("workflow 2")
        )

        assert response.status_code == 201
        assert response.json()["name"] == "new name"
        assert len(workflow_tr_in_db.content.links) == 2


@pytest.mark.asyncio
async def test_update_transformation_revision_with_released_component(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        store_single_transformation_revision(
            TransformationRevision(**tr_json_component_2)
        )

        async with async_test_client as ac:
            response = await ac.put(
                posix_urljoin(
                    "/api/transformations/", str(get_uuid_from_seed("component 2"))
                ),
                json=tr_json_component_2_update,
            )

        assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_transformation_revision_with_released_component_and_allow_overwrite_flag(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        store_single_transformation_revision(
            TransformationRevision(**tr_json_component_2)
        )

        async with async_test_client as ac:
            response = await ac.put(
                posix_urljoin(
                    "/api/transformations/", str(get_uuid_from_seed("component 2"))
                )
                + "?allow_overwrite_released=true",
                json=tr_json_component_2_update,
            )

        assert response.status_code == 201
        assert response.json()["name"] == "new name"
        assert response.json()["category"] == "Test"


@pytest.mark.asyncio
async def test_delete_transformation_revision_with_component(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        store_single_transformation_revision(
            TransformationRevision(**tr_json_component_3)
        )

        async with async_test_client as ac:
            response = await ac.delete(
                posix_urljoin(
                    "/api/transformations/", str(get_uuid_from_seed("component 3"))
                )
            )

        assert response.status_code == 204


@pytest.mark.asyncio
async def test_publish_transformation_revision_with_component(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        store_single_transformation_revision(
            TransformationRevision(**tr_json_component_3)
        )

        async with async_test_client as ac:
            response = await ac.put(
                posix_urljoin(
                    "/api/transformations/", str(get_uuid_from_seed("component 3"))
                ),
                json=tr_json_component_3_publish,
            )

        assert response.status_code == 201
        assert response.json()["state"] == "RELEASED"
        assert "released_timestamp" in response.json()["content"]


@pytest.mark.asyncio
async def test_deprecate_transformation_revision_with_component(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        store_single_transformation_revision(
            TransformationRevision(**tr_json_component_2)
        )

        async with async_test_client as ac:
            response = await ac.put(
                posix_urljoin(
                    "/api/transformations/", str(get_uuid_from_seed("component 2"))
                ),
                json=tr_json_component_2_deprecate,
            )

        assert response.status_code == 201
        assert response.json()["name"] != "new name"
        assert response.json()["category"] != "Test"
        assert "disabled_timestamp" in response.json()["content"]
        assert "released_timestamp" in response.json()["content"]


@pytest.mark.asyncio
async def test_execute_for_transformation_revision(
    async_test_client, clean_test_db_engine
):
    patched_session = sessionmaker(clean_test_db_engine)
    with mock.patch(
        "hetdesrun.persistence.dbservice.nesting.Session",
        patched_session,
    ):
        with mock.patch(
            "hetdesrun.persistence.dbservice.revision.Session",
            patched_session,
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

            async with async_test_client as ac:
                response = await ac.post(
                    "/api/transformations/execute",
                    json=json.loads(exec_by_id_input.json()),
                )

            assert response.status_code == 200
            resp_data = response.json()
            assert "output_types_by_output_name" in resp_data
            assert "job_id" in resp_data
            assert UUID(resp_data["job_id"]) == UUID(
                "1270547c-b224-461d-9387-e9d9d465bbe1"
            )


@pytest.mark.asyncio
async def test_execute_for_transformation_revision_with_job_id_none(
    async_test_client, clean_test_db_engine
):
    patched_session = sessionmaker(clean_test_db_engine)
    with mock.patch(
        "hetdesrun.persistence.dbservice.nesting.Session",
        patched_session,
    ):
        with mock.patch(
            "hetdesrun.persistence.dbservice.revision.Session",
            patched_session,
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
                job_id=None,
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


@pytest.mark.asyncio
async def test_execute_for_separate_runtime_container(
    async_test_client, clean_test_db_engine
):
    patched_session = sessionmaker(clean_test_db_engine)
    with mock.patch(
        "hetdesrun.persistence.dbservice.nesting.Session",
        patched_session,
    ):
        with mock.patch(
            "hetdesrun.persistence.dbservice.revision.Session",
            patched_session,
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
                    assert UUID(resp_data["job_id"]) == UUID(
                        "1270547c-b224-461d-9387-e9d9d465bbe1"
                    )
                    mocked_post.assert_called_once()


@pytest.mark.asyncio
async def test_execute_latest_for_transformation_revision_works(
    async_test_client, clean_test_db_engine
):
    patched_session = sessionmaker(clean_test_db_engine)
    with mock.patch(
        "hetdesrun.persistence.dbservice.nesting.Session",
        patched_session,
    ):
        with mock.patch(
            "hetdesrun.persistence.dbservice.revision.Session",
            patched_session,
        ):
            tr_component_1 = TransformationRevision(**tr_json_component_1)
            tr_component_1.content = update_code(tr_component_1)
            store_single_transformation_revision(tr_component_1)

            tr_component_1_new_revision = TransformationRevision(
                **tr_json_component_1_new_revision
            )
            tr_component_1_new_revision.content = update_code(
                tr_component_1_new_revision
            )
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
            assert (
                resp_data["output_types_by_output_name"]["operator_output"] == "STRING"
            )
            assert "job_id" in resp_data
            assert UUID(resp_data["job_id"]) == UUID(
                "1270547c-b224-461d-9387-e9d9d465bbe1"
            )


@pytest.mark.asyncio
async def test_execute_latest_for_transformation_revision_no_revision_in_db(
    async_test_client, clean_test_db_engine
):
    patched_session = sessionmaker(clean_test_db_engine)
    with mock.patch(
        "hetdesrun.persistence.dbservice.nesting.Session",
        patched_session,
    ):
        with mock.patch(
            "hetdesrun.persistence.dbservice.revision.Session",
            patched_session,
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
                "no released transformation revisions with revision group id"
                in response.json()["detail"]
            )


@pytest.mark.asyncio
async def test_execute_for_nested_workflow(async_test_client, clean_test_db_engine):
    patched_session = sessionmaker(clean_test_db_engine)
    with mock.patch(
        "hetdesrun.persistence.dbservice.nesting.Session",
        patched_session,
    ):
        with mock.patch(
            "hetdesrun.persistence.dbservice.revision.Session",
            patched_session,
        ):
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
                        )
                        + "?allow_overwrite_released=True",
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

                exec_by_id_input = ExecByIdInput(
                    id=workflow_id, wiring=tr_workflow.test_wiring
                )

                response = await ac.post(
                    "/api/transformations/execute",
                    json=json.loads(exec_by_id_input.json()),
                )

                assert response.status_code == 200
                assert "output_types_by_output_name" in response.json()
                assert response.json()["result"] == "ok"
                assert (
                    abs(
                        response.json()["output_results_by_output_name"]["intercept"]
                        - 2.88
                    )
                    < 0.01
                )
                assert (
                    response.json()["output_results_by_output_name"][
                        "before_step_detect"
                    ]
                    == {}
                )
                assert (
                    response.json()["output_results_by_output_name"][
                        "rul_regression_result_plot"
                    ]
                    == {}
                )


@pytest.mark.asyncio
async def test_put_workflow_transformation(async_test_client, clean_test_db_engine):
    patched_session = sessionmaker(clean_test_db_engine)
    with mock.patch(
        "hetdesrun.persistence.dbservice.nesting.Session",
        patched_session,
    ):
        with mock.patch(
            "hetdesrun.persistence.dbservice.revision.Session",
            patched_session,
        ):

            example_workflow_tr_json = load_json(
                "./transformations/workflows/examples/data-from-last-positive-step_100_2cbb87e7-ea99-4404-abe1-be550f22763f.json"
            )

            async with async_test_client as ac:
                response = await ac.put(
                    posix_urljoin(
                        "/api/transformations/", example_workflow_tr_json["id"]
                    ),
                    json=example_workflow_tr_json,
                )

            assert response.status_code == 201


@pytest.mark.asyncio
async def test_put_component_transformation_with_update_code(
    async_test_client, clean_test_db_engine
):
    patched_session = sessionmaker(clean_test_db_engine)
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        patched_session,
    ):

        path = "./tests/data/components/alerts-from-score_100_38f168ef-cb06-d89c-79b3-0cd823f32e9d.json"
        example_component_tr_json = load_json(path)

        async with async_test_client as ac:
            response = await ac.put(
                posix_urljoin("/api/transformations/", example_component_tr_json["id"])
                + "?update_component_code=True",
                json=example_component_tr_json,
            )

        component_tr_in_db = read_single_transformation_revision(
            example_component_tr_json["id"]
        )

        assert response.status_code == 201
        assert "COMPONENT_INFO" in response.json()["content"]
        assert "COMPONENT_INFO" in component_tr_in_db.content
        assert "register" not in response.json()["content"]
        assert "register" not in component_tr_in_db.content


@pytest.mark.asyncio
async def test_put_component_transformation_without_update_code(
    async_test_client, clean_test_db_engine
):
    patched_session = sessionmaker(clean_test_db_engine)
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        patched_session,
    ):

        path = "./tests/data/components/alerts-from-score_100_38f168ef-cb06-d89c-79b3-0cd823f32e9d.json"
        example_component_tr_json = load_json(path)

        async with async_test_client as ac:
            response = await ac.put(
                posix_urljoin("/api/transformations/", example_component_tr_json["id"])
                + "?update_component_code=False",
                json=example_component_tr_json,
            )

        component_tr_in_db = read_single_transformation_revision(
            example_component_tr_json["id"]
        )

        assert response.status_code == 201
        assert "COMPONENT_INFO" not in response.json()["content"]
        assert "COMPONENT_INFO" not in component_tr_in_db.content
        assert "register" in response.json()["content"]
        assert "register" in component_tr_in_db.content
