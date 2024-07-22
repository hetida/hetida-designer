import json
from copy import deepcopy
from posixpath import join as posix_urljoin
from uuid import UUID

import pytest

from hetdesrun.backend.models.component import ComponentRevisionFrontendDto
from hetdesrun.backend.models.wiring import WiringFrontendDto
from hetdesrun.backend.models.workflow import WorkflowRevisionFrontendDto
from hetdesrun.component.code import update_code
from hetdesrun.models.wiring import InputWiring, WorkflowWiring
from hetdesrun.persistence import get_db_engine
from hetdesrun.persistence.dbmodels import Base
from hetdesrun.persistence.dbservice.nesting import update_or_create_nesting
from hetdesrun.persistence.dbservice.revision import (
    read_single_transformation_revision,
    store_single_transformation_revision,
)
from hetdesrun.persistence.models.io import Connector
from hetdesrun.persistence.models.link import Link, Vertex
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.trafoutils.io.load import load_json
from hetdesrun.utils import get_uuid_from_seed
from hetdesrun.webservice.config import get_config


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
dto_json_component_1_publish = {
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
            "id": str(get_uuid_from_seed("new input")),
            "name": "new_input",
            "type": "INT",
        }
    ],
    "outputs": [],
    "wirings": [],
    "code": 'from hetdesrun.component.registration import register\nfrom hetdesrun.datatypes import DataType\n# add your own imports here, e.g.\n#     import pandas as pd\n#     import numpy as np\n\n\n# ***** DO NOT EDIT LINES BELOW *****\n# These lines may be overwritten if component details or inputs/outputs change."\n@register(\n    inputs={},\n    outputs={},\n    component_name="component 1",\n    description="description of component 1",\n    category="category",\n    uuid="c3f0ffdc-ff1c-a612-668c-0a606020ffaa",\n    group_id="b301ff9e-bdbb-8d7c-f6e2-7e83b919a8d3",\n    tag="1.0.0"\n)\ndef main(*, new_input):\n    # entrypoint function for this component\n    # ***** DO NOT EDIT LINES ABOVE *****\n    # write your function code here.\n    # new comment\n    pass\n',  # noqa: E501
}
dto_json_workflow_2_publishable = {
    "id": "c92da3cf-c9fb-9582-f9a2-c05d6e54bbd7",
    "groupId": "868988fc-b7d3-601b-cb05-d0f957d1733d",
    "name": "workflow 2",
    "description": "description of workflow 2",
    "category": "category",
    "type": "WORKFLOW",
    "state": "DRAFT",
    "tag": "1.0.0",
    "operators": [
        {
            "id": "57c194c3-6212-59a2-9404-48b44b4daa22",
            "groupId": "b301ff9e-bdbb-8d7c-f6e2-7e83b919a8d3",
            "name": "operator",
            "description": "",
            "category": "category",
            "type": "COMPONENT",
            "state": "RELEASED",
            "tag": "1.0.0",
            "itemId": "c3f0ffdc-ff1c-a612-668c-0a606020ffaa",
            "inputs": [
                {
                    "id": "88b58637-e5b6-1013-d12e-5bfdb9d949db",
                    "name": "operator_input",
                    "posX": 0,
                    "posY": 0,
                    "type": "INT",
                }
            ],
            "outputs": [
                {
                    "id": "a60c42e2-d0f3-34db-2707-0bf5954d3bce",
                    "name": "operator_output",
                    "posX": 0,
                    "posY": 0,
                    "type": "INT",
                }
            ],
            "posX": 0,
            "posY": 0,
        }
    ],
    "links": [
        {
            "id": "e8fb61ab-bfba-402e-9e7b-2df7d48fa6e7",
            "fromOperator": "c92da3cf-c9fb-9582-f9a2-c05d6e54bbd7",
            "fromConnector": "b1274e65-8cfa-47a7-92d7-c85b876eb167",
            "toOperator": "57c194c3-6212-59a2-9404-48b44b4daa22",
            "toConnector": "88b58637-e5b6-1013-d12e-5bfdb9d949db",
        },
        {
            "id": "06cfa9cb-11ef-44e7-ac45-8a9280a39ed0",
            "fromOperator": "57c194c3-6212-59a2-9404-48b44b4daa22",
            "fromConnector": "a60c42e2-d0f3-34db-2707-0bf5954d3bce",
            "toOperator": "c92da3cf-c9fb-9582-f9a2-c05d6e54bbd7",
            "toConnector": "755c17d7-daa6-437e-a05a-b3e1f3ed0f30",
        },
    ],
    "inputs": [
        {
            "id": "b1274e65-8cfa-47a7-92d7-c85b876eb167",
            "name": "input",
            "posX": 0,
            "posY": 0,
            "type": "INT",
            "operator": "57c194c3-6212-59a2-9404-48b44b4daa22",
            "connector": "88b58637-e5b6-1013-d12e-5bfdb9d949db",
            "constant": False,
        }
    ],
    "outputs": [
        {
            "id": "755c17d7-daa6-437e-a05a-b3e1f3ed0f30",
            "name": "output",
            "posX": 0,
            "posY": 0,
            "type": "INT",
            "operator": "57c194c3-6212-59a2-9404-48b44b4daa22",
            "connector": "a60c42e2-d0f3-34db-2707-0bf5954d3bce",
            "constant": False,
        }
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
            "filters": {"value": "100"},
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
    async_test_client, mocked_clean_test_db_session
):
    store_single_transformation_revision(
        WorkflowRevisionFrontendDto(**dto_json_workflow_1).to_transformation_revision()
    )

    async with async_test_client as ac:
        response = await ac.get("/api/workflows/" + str(get_uuid_from_seed("workflow 1")))
    assert response.status_code == 200
    assert response.json() == dto_json_workflow_1


@pytest.mark.asyncio
async def test_get_all_worfklow_revisions_with_valid_db_entries(
    async_test_client, mocked_clean_test_db_session
):
    store_single_transformation_revision(
        WorkflowRevisionFrontendDto(**dto_json_workflow_1).to_transformation_revision()
    )
    store_single_transformation_revision(
        WorkflowRevisionFrontendDto(**dto_json_workflow_2).to_transformation_revision()
    )

    async with async_test_client as ac:
        response = await ac.get("/api/workflows/")
    assert response.status_code == 200
    assert response.json()[0] == dto_json_workflow_1
    assert response.json()[1] == dto_json_workflow_2


@pytest.mark.asyncio
async def test_get_workflow_revision_by_id_with_inexistent_workflow(
    async_test_client, mocked_clean_test_db_session
):
    async with async_test_client as ac:
        response = await ac.get("/api/workflows/" + str(get_uuid_from_seed("inexistent workflow")))
    assert response.status_code == 404
    assert "Found no" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_transformation_revision_from_workflow_dto(
    async_test_client, mocked_clean_test_db_session
):
    async with async_test_client as ac:
        response = await ac.post("/api/workflows/", json=dto_json_workflow_1)

    assert response.status_code == 201
    assert response.json()["name"] == dto_json_workflow_1["name"]


@pytest.mark.asyncio
async def test_update_transformation_revision_from_workflow_dto(
    async_test_client, mocked_clean_test_db_session
):
    store_single_transformation_revision(
        ComponentRevisionFrontendDto(**dto_json_component_1).to_transformation_revision()
    )
    store_single_transformation_revision(
        WorkflowRevisionFrontendDto(**dto_json_workflow_2).to_transformation_revision()
    )

    async with async_test_client as ac:
        response = await ac.put(
            "/api/workflows/" + str(get_uuid_from_seed("workflow 2")),
            json=dto_json_workflow_2_update,
        )

    assert response.status_code == 201
    assert response.json()["operators"][0]["id"] == str(get_uuid_from_seed("operator"))
    assert "name" not in response.json()["inputs"][0]
    assert "name" not in response.json()["outputs"][0]


@pytest.mark.asyncio
async def test_update_transformation_revision_from_non_existing_workflow_dto(
    async_test_client, mocked_clean_test_db_session
):
    store_single_transformation_revision(
        ComponentRevisionFrontendDto(**dto_json_component_1).to_transformation_revision()
    )

    async with async_test_client as ac:
        response = await ac.put(
            "/api/workflows/" + str(get_uuid_from_seed("workflow 2")),
            json=dto_json_workflow_2_update,
        )

    assert response.status_code == 201
    assert response.json()["operators"][0]["id"] == str(get_uuid_from_seed("operator"))
    assert "name" not in response.json()["inputs"][0]
    assert "name" not in response.json()["outputs"][0]


@pytest.mark.asyncio
async def test_update_transformation_revision_from_released_workflow_dto(
    async_test_client, mocked_clean_test_db_session
):
    store_single_transformation_revision(
        WorkflowRevisionFrontendDto(**dto_json_workflow_1).to_transformation_revision()
    )

    async with async_test_client as ac:
        response = await ac.put(
            "/api/workflows/" + str(get_uuid_from_seed("workflow 1")),
            json=dto_json_workflow_1_update,
        )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_delete_multiple_inputs_of_wf_at_once(
    async_test_client, mocked_clean_test_db_session
):
    json_files = [
        "./transformations/components/visualization/2d-grid-generator_100_096c6181-4ba5-0ee7-361a-3c32eee8c0c2.json",
        "./transformations/components/connectors/name-series_100_a4064897-66d3-9601-328e-5ae9036665c5.json",
        "./transformations/components/connectors/combine-into-dataframe_100_68f91351-a1f5-9959-414a-2c72003f3226.json",
        "./transformations/components/connectors/combine-as-named-column-into-dataframe_100_0d08af64-3f34-cddc-354b-d6a26c3f1aab.json",
        "./transformations/components/anomaly-detection/isolation-forest_100_cdec1d55-5bb6-8e8d-4571-fbc0ebf5a354.json",
        "./transformations/components/visualization/contour-plot_100_f7530499-51b2-dd01-0d21-c24ee6f8c37e.json",
        "./transformations/components/connectors/forget_100_d1fb4ae5-ef27-26b8-7a58-40b7cd8412e7.json",
    ]
    for file in json_files:
        tr_json = load_json(file)
        store_single_transformation_revision(TransformationRevision(**tr_json))

    with open(  # noqa: UP015
        "./tests/data/workflows/iso_forest_wf_dto.json", "r", encoding="utf8"
    ) as f:
        wf_dto_json = json.load(f)

    wf_dto_json["state"] = "DRAFT"

    store_single_transformation_revision(
        WorkflowRevisionFrontendDto(**wf_dto_json).to_transformation_revision()
    )

    assert wf_dto_json["inputs"][3]["name"] == "x_max"
    wf_dto_json["inputs"][3]["name"] = ""
    assert wf_dto_json["inputs"][4]["name"] == "x_min"
    wf_dto_json["inputs"][4]["name"] = ""

    updated_wf_dto = WorkflowRevisionFrontendDto(**wf_dto_json)

    assert updated_wf_dto.inputs[3].name == ""
    assert updated_wf_dto.inputs[4].name == ""

    async with async_test_client as ac:
        response = await ac.put(
            "/api/workflows/" + str(wf_dto_json["id"]),
            json=wf_dto_json,
        )

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_publish_transformation_revision_from_workflow_dto(
    async_test_client, mocked_clean_test_db_session
):
    store_single_transformation_revision(
        ComponentRevisionFrontendDto(**dto_json_component_1_publish).to_transformation_revision()
    )
    store_single_transformation_revision(
        WorkflowRevisionFrontendDto(**dto_json_workflow_2_publishable).to_transformation_revision()
    )

    dto_json_workflow_2_publish = deepcopy(dto_json_workflow_2_publishable)
    dto_json_workflow_2_publish["state"] = "RELEASED"
    print()

    async with async_test_client as ac:
        response = await ac.put(
            "/api/workflows/" + str(get_uuid_from_seed("workflow 2")),
            json=dto_json_workflow_2_publish,
        )

    assert response.status_code == 201
    assert response.json()["state"] == "RELEASED"
    assert response.json()["name"] != "new name"


@pytest.mark.asyncio
async def test_deprecate_transformation_revision_from_workflow_dto(
    async_test_client, mocked_clean_test_db_session
):
    store_single_transformation_revision(
        WorkflowRevisionFrontendDto(**dto_json_workflow_1).to_transformation_revision()
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
    async_test_client, mocked_clean_test_db_session
):
    store_single_transformation_revision(
        WorkflowRevisionFrontendDto(**dto_json_workflow_2).to_transformation_revision()
    )

    async with async_test_client as ac:
        response = await ac.delete(
            "/api/workflows/" + str(get_uuid_from_seed("workflow 2")),
        )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_set_test_wiring_to_workflow(async_test_client, mocked_clean_test_db_session):
    store_single_transformation_revision(
        ComponentRevisionFrontendDto(**dto_json_component_1).to_transformation_revision()
    )
    store_single_transformation_revision(
        WorkflowRevisionFrontendDto(**dto_json_workflow_2_update).to_transformation_revision()
    )

    async with async_test_client as ac:
        response = await ac.post(
            "/api/workflows/" + str(get_uuid_from_seed("workflow 2")) + "/wirings",
            json=dto_json_wiring,
        )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_execute_for_workflow_dto(async_test_client, mocked_clean_test_db_session):
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
                connector=Connector(**tr_workflow_2.content.inputs[0].dict()),
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
                connector=Connector(**tr_workflow_2.content.outputs[0].dict()),
            ),
        )
    )
    tr_workflow_2.io_interface.inputs[0].name = "wf_input"
    tr_workflow_2.io_interface.outputs[0].name = "wf_output"

    store_single_transformation_revision(tr_workflow_2)

    update_or_create_nesting(tr_workflow_2)
    async with async_test_client as ac:
        response = await ac.post(
            "/api/workflows/" + str(get_uuid_from_seed("workflow 2")) + "/execute",
            json=dto_json_wiring,
        )

    assert response.status_code == 200
    assert "output_types_by_output_name" in response.json()


@pytest.mark.asyncio
async def test_execute_for_full_workflow_dto(async_test_client, mocked_clean_test_db_session):
    async with async_test_client as ac:
        json_files = [
            "./transformations/components/connectors/pass-through-float_100_2f511674-f766-748d-2de3-ad5e62e10a1a.json",
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

        workflow_id = UUID("3d504361-e351-4d52-8734-391aa47e8f24")
        tr_workflow = read_single_transformation_revision(workflow_id)
        wiring_dto = WiringFrontendDto.from_wiring(tr_workflow.test_wiring, workflow_id)

        response = await ac.post(
            "/api/workflows/" + str(workflow_id) + "/execute",
            json=json.loads(wiring_dto.json(by_alias=True)),
        )

        assert response.status_code == 200
        assert "output_types_by_output_name" in response.json()


@pytest.mark.asyncio
async def test_execute_for_full_workflow_dto_with_nan(
    async_test_client, mocked_clean_test_db_session
):
    async with async_test_client as ac:
        json_files = [
            "./transformations/components/arithmetic/consecutive-differences_100_ce801dcb-8ce1-14ad-029d-a14796dcac92.json",
            "./transformations/components/basic/filter_100_18260aab-bdd6-af5c-cac1-7bafde85188f.json",
            "./transformations/components/basic/greater-or-equal_100_f759e4c0-1468-0f2e-9740-41302b860193.json",
            "./transformations/components/basic/last-datetime-index_100_c8e3bc64-b214-6486-31db-92a8888d8991.json",
            "./transformations/components/basic/restrict-to-time-interval_100_bf469c0a-d17c-ca6f-59ac-9838b2ff67ac.json",
            "./transformations/components/connectors/pass-through-float_100_2f511674-f766-748d-2de3-ad5e62e10a1a.json",
            "./transformations/components/connectors/pass-through-series_100_bfa27afc-dea8-b8aa-4b15-94402f0739b6.json",
            "./transformations/workflows/examples/data-from-last-positive-step_100_2cbb87e7-ea99-4404-abe1-be550f22763f.json",
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

        workflow_id = UUID("2cbb87e7-ea99-4404-abe1-be550f22763f")
        wiring_dto = WiringFrontendDto.from_wiring(
            WorkflowWiring(
                input_wirings=[
                    InputWiring(
                        adapter_id="direct_provisioning",
                        workflow_input_name="inp_series",
                        filters={
                            "value": '{"2020-05-01T00:00:00.000Z": 1.2, "2020-05-01T01:00:00.000Z": 3.14, "2020-05-01T02:00:00.000Z": 5, "2020-05-01T03:00:00.000Z": null}'  # noqa: E501
                        },
                    ),
                    InputWiring(
                        adapter_id="direct_provisioning",
                        workflow_input_name="positive_step_size",
                        filters={"value": "0.2"},
                    ),
                ],
                output_wirings=[],
            ),
            workflow_id,
        )

        response = await ac.post(
            "/api/workflows/" + str(workflow_id) + "/execute",
            json=json.loads(wiring_dto.json(by_alias=True)),
        )

        assert response.status_code == 200
        assert "output_results_by_output_name" in response.json()
        output_results_by_output_name = response.json()["output_results_by_output_name"]
        assert "series_from_last_step" in output_results_by_output_name
        assert (
            len(output_results_by_output_name["series_from_last_step"]["__data__"])
            == 3  # split orient
        )
        assert (
            output_results_by_output_name["series_from_last_step"]["__data__"]["data"][1] == None  # noqa: E711
        )
