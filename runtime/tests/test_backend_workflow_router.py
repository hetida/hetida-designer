from unittest import mock
import pytest

from starlette.testclient import TestClient

from typing import List
from uuid import UUID
import os
import json

from hetdesrun.utils import ComponentDTO, IODTO, load_data, get_uuid_from_seed

from hetdesrun.webservice.application import app

from hetdesrun.persistence import get_db_engine, sessionmaker

from hetdesrun.persistence.models.io import Connector
from hetdesrun.persistence.models.link import Link, Vertex

from hetdesrun.persistence.dbmodels import Base
from hetdesrun.persistence.dbservice.revision import (
    store_single_transformation_revision,
    read_single_transformation_revision,
)
from hetdesrun.persistence.dbservice.nesting import update_or_create_nesting

from hetdesrun.backend.service.transformation_router import generate_code
from hetdesrun.backend.models.workflow import WorkflowRevisionFrontendDto
from hetdesrun.backend.models.component import ComponentRevisionFrontendDto
from hetdesrun.backend.models.wiring import WiringFrontendDto

client = TestClient(app)


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


dto_json_workflow_1 = {
    "id": str(get_uuid_from_seed("workflow 1")),
    "groupId": str(get_uuid_from_seed("group of workflow 1")),
    "name": "workflow 1",
    "description": "description of workflow 1",
    "category": "category",
    "type": "WORKFLOW",
    "state": "RELEASED",
    "tag": "1.0.0",
    "operators": [],
    "links": [],
    "inputs": [],
    "outputs": [],
    "wirings": [],
}
dto_json_workflow_1_update = {
    "id": str(get_uuid_from_seed("workflow 1")),
    "groupId": str(get_uuid_from_seed("group of workflow 1")),
    "name": "new name",
    "description": "description of workflow 1",
    "category": "category",
    "type": "WORKFLOW",
    "state": "RELEASED",
    "tag": "1.0.0",
    "operators": [],
    "links": [],
    "inputs": [],
    "outputs": [],
    "wirings": [],
}
dto_json_workflow_1_deprecate = {
    "id": str(get_uuid_from_seed("workflow 1")),
    "groupId": str(get_uuid_from_seed("group of workflow 1")),
    "name": "new name",
    "description": "description of workflow 1",
    "category": "category",
    "type": "WORKFLOW",
    "state": "DISABLED",
    "tag": "1.0.0",
    "operators": [],
    "links": [],
    "inputs": [],
    "outputs": [],
    "wirings": [],
}
dto_json_workflow_2 = {
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
    "operators": [],
    "wirings": [],
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
    "wirings": [],
}

dto_json_wiring = {
    "id": "2634db74-157b-4c07-a49d-6aedc6f9a7bc",
    "name": "STANDARD-WIRING",
    "inputWirings": [
        {
            "id": str(get_uuid_from_seed("input wiring")),
            "workflowInputName": "wf_input",
            "adapterId": "direct_provisioning",
            "filters": {"value": 100},
        },
    ],
    "outputWirings": [
        {
            "id": str(get_uuid_from_seed("output wiring")),
            "workflowOutputName": "wf_output",
            "adapterId": "direct_provisioning",
        },
    ],
}
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


@pytest.mark.asyncio
async def test_get_workflow_revision_without_content_by_id_with_valid_workflow(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        store_single_transformation_revision(
            WorkflowRevisionFrontendDto(
                **dto_json_workflow_1
            ).to_transformation_revision()
        )

        async with async_test_client as ac:
            response = await ac.get(
                "/api/workflows/" + str(get_uuid_from_seed("workflow 1"))
            )
        assert response.status_code == 200
        assert response.json() == dto_json_workflow_1


@pytest.mark.asyncio
async def test_get_all_worfklow_revisions_with_valid_db_entries(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        store_single_transformation_revision(
            WorkflowRevisionFrontendDto(
                **dto_json_workflow_1
            ).to_transformation_revision()
        )
        store_single_transformation_revision(
            WorkflowRevisionFrontendDto(
                **dto_json_workflow_2
            ).to_transformation_revision()
        )

        async with async_test_client as ac:
            response = await ac.get("/api/workflows/")
        assert response.status_code == 200
        assert response.json()[0] == dto_json_workflow_1
        assert response.json()[1] == dto_json_workflow_2


@pytest.mark.asyncio
async def test_get_workflow_revision_by_id_with_inexistent_workflow(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        async with async_test_client as ac:
            response = await ac.get(
                "/api/workflows/" + str(get_uuid_from_seed("inexistent workflow"))
            )
        assert response.status_code == 404
        assert "Found no" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_transformation_revision_from_workflow_dto(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):

        async with async_test_client as ac:
            response = await ac.post("/api/workflows/", json=dto_json_workflow_1)

        assert response.status_code == 201
        assert response.json()["name"] == dto_json_workflow_1["name"]


@pytest.mark.asyncio
async def test_update_transformation_revision_from_workflow_dto(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        store_single_transformation_revision(
            WorkflowRevisionFrontendDto(
                **dto_json_workflow_2
            ).to_transformation_revision()
        )

        async with async_test_client as ac:
            response = await ac.put(
                "/api/workflows/" + str(get_uuid_from_seed("workflow 2")),
                json=dto_json_workflow_2_update,
            )

        assert response.status_code == 201
        assert response.json()["operators"][0]["id"] == str(
            get_uuid_from_seed("operator")
        )
        assert "name" not in response.json()["inputs"][0]
        assert "name" not in response.json()["outputs"][0]


@pytest.mark.asyncio
async def test_update_transformation_revision_from_non_existing_workflow_dto(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        async with async_test_client as ac:
            response = await ac.put(
                "/api/workflows/" + str(get_uuid_from_seed("workflow 2")),
                json=dto_json_workflow_2_update,
            )

        assert response.status_code == 201
        assert response.json()["operators"][0]["id"] == str(
            get_uuid_from_seed("operator")
        )
        assert "name" not in response.json()["inputs"][0]
        assert "name" not in response.json()["outputs"][0]


@pytest.mark.asyncio
async def test_update_transformation_revision_from_released_workflow_dto(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        store_single_transformation_revision(
            WorkflowRevisionFrontendDto(
                **dto_json_workflow_1
            ).to_transformation_revision()
        )

        async with async_test_client as ac:
            response = await ac.put(
                "/api/workflows/" + str(get_uuid_from_seed("workflow 1")),
                json=dto_json_workflow_1_update,
            )

        assert response.status_code == 403


@pytest.mark.asyncio
async def test_deprecate_transformation_revision_from_workflow_dto(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        store_single_transformation_revision(
            WorkflowRevisionFrontendDto(
                **dto_json_workflow_1
            ).to_transformation_revision()
        )

        async with async_test_client as ac:
            response = await ac.put(
                "/api/workflows/" + str(get_uuid_from_seed("workflow 1")),
                json=dto_json_workflow_1_deprecate,
            )

        assert response.status_code == 201
        assert response.json()["state"] == "DISABLED"
        assert response.json()["name"] != "new name"


@pytest.mark.asyncio
async def test_delete_transformation_revision_from_workflow_dto(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        store_single_transformation_revision(
            WorkflowRevisionFrontendDto(
                **dto_json_workflow_2
            ).to_transformation_revision()
        )

        async with async_test_client as ac:
            response = await ac.delete(
                "/api/workflows/" + str(get_uuid_from_seed("workflow 2")),
            )

        assert response.status_code == 204


@pytest.mark.asyncio
async def test_set_test_wiring_to_workflow(async_test_client, clean_test_db_engine):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):

        store_single_transformation_revision(
            WorkflowRevisionFrontendDto(
                **dto_json_workflow_2_update
            ).to_transformation_revision()
        )

        async with async_test_client as ac:
            response = await ac.post(
                "/api/workflows/" + str(get_uuid_from_seed("workflow 2")) + "/wirings",
                json=dto_json_wiring,
            )

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_execute_for_workflow_dto(async_test_client, clean_test_db_engine):
    patched_session = sessionmaker(clean_test_db_engine)
    with mock.patch(
        "hetdesrun.persistence.dbservice.nesting.Session", patched_session,
    ):
        with mock.patch(
            "hetdesrun.persistence.dbservice.revision.Session", patched_session,
        ):
            component_dto = ComponentRevisionFrontendDto(**dto_json_component_1)
            component_dto.code = generate_code(component_dto.to_code_body())
            store_single_transformation_revision(
                component_dto.to_transformation_revision()
            )
            tr_workflow_2 = WorkflowRevisionFrontendDto(
                **dto_json_workflow_2_update
            ).to_transformation_revision()
            tr_workflow_2.content.inputs[0].name = "wf_input"
            tr_workflow_2.content.outputs[0].name = "wf_output"
            tr_workflow_2.content.links.append(
                Link(
                    start=Vertex(
                        operator=None,
                        connector=Connector.from_io(tr_workflow_2.content.inputs[0]),
                    ),
                    end=Vertex(
                        operator=tr_workflow_2.content.operators[0].id,
                        connector=tr_workflow_2.content.operators[0].inputs[0],
                    ),
                )
            )
            tr_workflow_2.content.links.append(
                Link(
                    start=Vertex(
                        operator=tr_workflow_2.content.operators[0].id,
                        connector=tr_workflow_2.content.operators[0].outputs[0],
                    ),
                    end=Vertex(
                        operator=None,
                        connector=Connector.from_io(tr_workflow_2.content.outputs[0]),
                    ),
                )
            )
            tr_workflow_2.io_interface.inputs[0].name = "wf_input"
            tr_workflow_2.io_interface.outputs[0].name = "wf_output"

            store_single_transformation_revision(tr_workflow_2)

            update_or_create_nesting(tr_workflow_2)

            async with async_test_client as ac:
                response = await ac.post(
                    "/api/workflows/"
                    + str(get_uuid_from_seed("workflow 2"))
                    + "/execute",
                    json=dto_json_wiring,
                )

            assert response.status_code == 200
            assert "output_types_by_output_name" in response.json()


@pytest.mark.asyncio
async def test_execute_for_full_workflow_dto(async_test_client, clean_test_db_engine):
    patched_session = sessionmaker(clean_test_db_engine)
    with mock.patch(
        "hetdesrun.persistence.dbservice.nesting.Session", patched_session,
    ):
        with mock.patch(
            "hetdesrun.persistence.dbservice.revision.Session", patched_session,
        ):
            async with async_test_client as ac:
                base_path_components = "components"
                component_categories: List[str] = [
                    "Connectors",
                    "Connectors",
                    "Connectors",
                    "Remaining_Useful_Life",
                    "Visualization",
                    "Arithmetic",
                    "Basic",
                    "Basic",
                    "Basic",
                    "Basic",
                    "Connectors",
                    # "Connectors",
                    # "Connectors",
                    "Visualization",
                ]
                component_file_names_without_ext: List[str] = [
                    "pass_through_int",
                    "pass_through_series",
                    "pass_through_string",
                    "univariate_linear_rul_regression",
                    "univariate_linear_rul_regression_plot",
                    "consecutive_differences",
                    "filter",
                    "greater_or_equal",
                    "last_datetime_index",
                    "restrict_to_time_interval",
                    "pass_through_float",
                    # "pass_through_series",
                    # "pass_through_series",
                    "single_timeseries_plot",
                ]

                for index in range(len(component_file_names_without_ext)):
                    path_without_ext = os.path.join(
                        base_path_components,
                        component_categories[index],
                        component_file_names_without_ext[index],
                    )
                    component_json_file = path_without_ext + ".json"
                    component_doc_file = path_without_ext + ".md"
                    component_code_file = path_without_ext + ".py"

                    base_name = os.path.basename(path_without_ext)
                    category = component_categories[index]
                    info, doc, code = load_data(
                        component_json_file, component_doc_file, component_code_file
                    )

                    comp_id = get_uuid_from_seed("component_" + base_name)
                    # add IDs to inputs
                    info["inputs"] = [
                        IODTO(
                            **input,
                            id=get_uuid_from_seed(
                                "component_input_" + base_name + "_" + input["name"]
                            ),
                        )
                        for input in info["inputs"]
                    ]

                    # add IDs to outputs
                    info["outputs"] = [
                        IODTO(
                            **output,
                            id=get_uuid_from_seed(
                                "component_output_" + base_name + "_" + output["name"]
                            ),
                        )
                        for output in info["outputs"]
                    ]

                    comp_dto = ComponentDTO(
                        **info,
                        category=category.replace("_", " "),
                        code=code,
                        groupId=comp_id,
                        id=comp_id,
                        tag="1.0.0",
                    )

                    response = await ac.put(
                        "/api/components/" + str(comp_id),
                        json=json.loads(comp_dto.json()),
                    )

                base_path_workflows = ["workflows", "workflows", "workflows2"]
                workflow_categories = ["Examples", "Examples", "Examples"]
                workflow_file_names_without_ext = [
                    "Univariate_Linear_RUL_Regression_Example",
                    "Data_From_Last_Positive_Step",
                    "Linear_RUL_From_Last_Positive_Step",
                ]
                workflow_ids: List[UUID] = []
                for index in range(len(workflow_file_names_without_ext)):
                    path_without_ext = os.path.join(
                        base_path_workflows[index],
                        workflow_categories[index],
                        workflow_file_names_without_ext[index],
                    )
                    base_name = os.path.basename(path_without_ext)

                    workflow_json_file = path_without_ext + ".json"
                    workflow_doc_file = path_without_ext + ".md"

                    info, doc, _ = load_data(workflow_json_file, workflow_doc_file)

                    workflow_id = info["id"]

                    response = await ac.put(
                        "/api/workflows/" + str(workflow_id), json=info
                    )

                    workflow_ids.append(workflow_id)

                workflow_id = workflow_ids[2]
                tr_workflow = read_single_transformation_revision(workflow_id)
                wiring_dto = WiringFrontendDto.from_wiring(
                    tr_workflow.test_wiring, workflow_id
                )

                response = await ac.post(
                    "/api/workflows/" + workflow_id + "/execute",
                    json=json.loads(wiring_dto.json(by_alias=True)),
                )

                assert response.status_code == 200
                assert "output_types_by_output_name" in response.json()
