import pytest

from hetdesrun.backend.models.component import ComponentRevisionFrontendDto
from hetdesrun.backend.models.workflow import WorkflowRevisionFrontendDto
from hetdesrun.persistence import get_db_engine
from hetdesrun.persistence.dbmodels import Base
from hetdesrun.persistence.dbservice.revision import (
    store_single_transformation_revision,
)
from hetdesrun.utils import get_uuid_from_seed


@pytest.fixture()
def clean_test_db_engine(use_in_memory_db):
    if use_in_memory_db:
        in_memory_database_url = "sqlite+pysqlite:///:memory:"
        engine = get_db_engine(override_db_url=in_memory_database_url)
    else:
        engine = get_db_engine()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    return engine


dto_json_component_1 = {
    "id": str(get_uuid_from_seed("component 1")),
    "groupId": str(get_uuid_from_seed("group of component 1")),
    "name": "new name",
    "description": "description of component 1",
    "category": "Test",
    "type": "COMPONENT",
    "state": "RELEASED",
    "tag": "1.0.0",
    "inputs": [
        {
            "id": str(get_uuid_from_seed("operator input")),
            "name": "operator_input",
            "type": "INT",
        }
    ],
    "outputs": [
        {
            "id": str(get_uuid_from_seed("operator output")),
            "name": "operator_output",
            "type": "INT",
        }
    ],
    "wirings": [],
    "code": "",
}

dto_json_workflow_2_update = {
    "id": str(get_uuid_from_seed("workflow 2")),
    "groupId": str(get_uuid_from_seed("group of workflow 2")),
    "name": "workflow 2",
    "description": "description of workflow 2",
    "category": "category",
    "type": "WORKFLOW",
    "state": "DRAFT",
    "tag": "1.0.0",
    "links": [],
    "inputs": [],
    "outputs": [],
    "operators": [
        {
            "id": str(get_uuid_from_seed("operator")),
            "groupId": str(get_uuid_from_seed("group of component 1")),
            "name": "operator",
            "description": "",
            "category": "category",
            "type": "COMPONENT",
            "state": "RELEASED",
            "tag": "1.0.0",
            "itemId": str(get_uuid_from_seed("component 1")),
            "inputs": [
                {
                    "id": str(get_uuid_from_seed("operator input")),
                    "name": "operator_input",
                    "type": "INT",
                    "posX": 0,
                    "posY": 0,
                },
            ],
            "outputs": [
                {
                    "id": str(get_uuid_from_seed("operator output")),
                    "name": "operator_output",
                    "type": "INT",
                    "posX": 0,
                    "posY": 0,
                },
            ],
            "posX": 0,
            "posY": 0,
        },
    ],
    "wirings": [
        {
            "id": str(get_uuid_from_seed("workflow 2")),
            "name": "STANDARD-WIRING",
            "inputWirings": [
                {
                    "id": "5021c197-3c38-4e66-b4dc-20e6b5a75bdc",
                    "workflowInputName": "operator_input",
                    "adapterId": "direct_provisioning",
                    "filters": {"value": "100"},
                },
            ],
            "outputWirings": [
                {
                    "id": "4c6034e9-1f58-4b98-b6a5-68231a41e08a",
                    "workflowOutputName": "operator_output",
                    "adapterId": "direct_provisioning",
                },
            ],
        }
    ],
}

dto_json_wiring = {
    "id": str(get_uuid_from_seed("workflow 2")),
    "name": "STANDARD-WIRING",
    "inputWirings": [
        {
            "id": "5021c197-3c38-4e66-b4dc-20e6b5a75bdc",
            "workflowInputName": "operator_input",
            "adapterId": "direct_provisioning",
            "filters": {"value": "100"},
        },
    ],
    "outputWirings": [
        {
            "id": "4c6034e9-1f58-4b98-b6a5-68231a41e08a",
            "workflowOutputName": "operator_output",
            "adapterId": "direct_provisioning",
        },
    ],
}


@pytest.mark.asyncio
async def test_update_wiring(async_test_client, mocked_clean_test_db_session):
    store_single_transformation_revision(
        ComponentRevisionFrontendDto(**dto_json_component_1).to_transformation_revision()
    )
    store_single_transformation_revision(
        WorkflowRevisionFrontendDto(**dto_json_workflow_2_update).to_transformation_revision()
    )

    async with async_test_client as ac:
        response = await ac.put(
            "/api/wirings/" + str(get_uuid_from_seed("workflow 2")),
            json=dto_json_wiring,
        )

    assert response.status_code == 200
    assert len(response.json()["inputWirings"]) == len(dto_json_wiring["inputWirings"])
    assert len(response.json()["outputWirings"]) == len(dto_json_wiring["outputWirings"])
