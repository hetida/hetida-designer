import json
from posixpath import join as posix_urljoin
from unittest import mock
from uuid import UUID

import pytest

from hetdesrun.backend.models.component import ComponentRevisionFrontendDto
from hetdesrun.backend.models.wiring import WiringFrontendDto
from hetdesrun.backend.models.workflow import WorkflowRevisionFrontendDto
from hetdesrun.component.code import update_code
from hetdesrun.exportimport.importing import load_json
from hetdesrun.persistence import get_db_engine, sessionmaker
from hetdesrun.persistence.dbmodels import Base
from hetdesrun.persistence.dbservice.nesting import update_or_create_nesting
from hetdesrun.persistence.dbservice.revision import (
    read_single_transformation_revision,
    store_single_transformation_revision,
)
from hetdesrun.persistence.models.io import Connector
from hetdesrun.persistence.models.link import Link, Vertex
from hetdesrun.utils import get_uuid_from_seed
from hetdesrun.webservice.config import get_config


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
        "hetdesrun.persistence.dbservice.nesting.Session",
        patched_session,
    ):
        with mock.patch(
            "hetdesrun.persistence.dbservice.revision.Session",
            patched_session,
        ):
            component_dto = ComponentRevisionFrontendDto(**dto_json_component_1)
            tr_component = component_dto.to_transformation_revision()
            tr_component.content = update_code(tr_component)
            store_single_transformation_revision(tr_component)
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

                workflow_id = UUID("3d504361-e351-4d52-8734-391aa47e8f24")
                tr_workflow = read_single_transformation_revision(workflow_id)
                wiring_dto = WiringFrontendDto.from_wiring(
                    tr_workflow.test_wiring, workflow_id
                )

                response = await ac.post(
                    "/api/workflows/" + str(workflow_id) + "/execute",
                    json=json.loads(wiring_dto.json(by_alias=True)),
                )

                assert response.status_code == 200
                assert "output_types_by_output_name" in response.json()
