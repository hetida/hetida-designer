from unittest import mock
import pytest

from starlette.testclient import TestClient

from hetdesrun.utils import get_uuid_from_seed

from hetdesrun.webservice.application import app

from hetdesrun.exportimport.importing import load_json

from hetdesrun.component.code import update_code

from hetdesrun.persistence import get_db_engine, sessionmaker
from hetdesrun.persistence.dbmodels import Base
from hetdesrun.persistence.dbservice.revision import (
    store_single_transformation_revision,
)
from hetdesrun.persistence.models.transformation import TransformationRevision

from hetdesrun.backend.models.component import ComponentRevisionFrontendDto

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


dto_json_component_1 = {
    "id": str(get_uuid_from_seed("component 1")),
    "groupId": str(get_uuid_from_seed("group of component 1")),
    "name": "component 1",
    "description": "description of component 1",
    "category": "category",
    "type": "COMPONENT",
    "state": "DRAFT",
    "tag": "1.0.0",
    "inputs": [],
    "outputs": [],
    "wirings": [],
    "code": "code",
}
dto_json_component_1_update = {
    "id": str(get_uuid_from_seed("component 1")),
    "groupId": str(get_uuid_from_seed("group of component 1")),
    "name": "new name",
    "description": "description of component 1",
    "category": "Test",
    "type": "COMPONENT",
    "state": "DRAFT",
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
    "code": 'from hetdesrun.component.registration import register\nfrom hetdesrun.datatypes import DataType\n# add your own imports here, e.g.\n#     import pandas as pd\n#     import numpy as np\n\n\n# ***** DO NOT EDIT LINES BELOW *****\n# These lines may be overwritten if component details or inputs/outputs change."\n@register(\n    inputs={},\n    outputs={},\n    component_name="component 1",\n    description="description of component 1",\n    category="category",\n    uuid="c3f0ffdc-ff1c-a612-668c-0a606020ffaa",\n    group_id="b301ff9e-bdbb-8d7c-f6e2-7e83b919a8d3",\n    tag="1.0.0"\n)\ndef main(*, new_input):\n    # entrypoint function for this component\n    # ***** DO NOT EDIT LINES ABOVE *****\n    # write your function code here.\n    # new comment\n    pass\n',
}
dto_json_component_2 = {
    "id": str(get_uuid_from_seed("component 2")),
    "groupId": str(get_uuid_from_seed("group of component 2")),
    "name": "component 2",
    "description": "description of component 2",
    "category": "category",
    "type": "COMPONENT",
    "state": "RELEASED",
    "tag": "1.0.0",
    "inputs": [],
    "outputs": [],
    "wirings": [],
    "code": "code",
}
dto_json_component_2_update = {
    "id": str(get_uuid_from_seed("component 2")),
    "groupId": str(get_uuid_from_seed("group of component 2")),
    "name": "component 2",
    "description": "description of component 2",
    "category": "category",
    "type": "COMPONENT",
    "state": "RELEASED",
    "tag": "1.0.0",
    "inputs": [],
    "outputs": [],
    "wirings": [],
    "code": 'from hetdesrun.component.registration import register\nfrom hetdesrun.datatypes import DataType\n# add your own imports here, e.g.\n#     import pandas as pd\n#     import numpy as np\n\n\n# ***** DO NOT EDIT LINES BELOW *****\n# These lines may be overwritten if component details or inputs/outputs change."\n@register(\n    inputs={},\n    outputs={},\n    component_name="component 2",\n    description="description of component 2",\n    category="category",\n    uuid="'
    + str(get_uuid_from_seed("component 2"))
    + '",\n    group_id="'
    + str(get_uuid_from_seed("group of component 2"))
    + '",\n    tag="1.0.0"\n)\ndef main(*):\n    # entrypoint function for this component\n    # ***** DO NOT EDIT LINES ABOVE *****\n    # write your function code here.\n    # new comment\n    pass\n',
}
dto_json_component_2_deprecate = {
    "id": str(get_uuid_from_seed("component 2")),
    "groupId": str(get_uuid_from_seed("group of component 2")),
    "name": "component 2",
    "description": "description of component 2",
    "category": "category",
    "type": "COMPONENT",
    "state": "DISABLED",
    "tag": "1.0.0",
    "inputs": [],
    "outputs": [],
    "wirings": [],
    "code": 'from hetdesrun.component.registration import register\nfrom hetdesrun.datatypes import DataType\n# add your own imports here, e.g.\n#     import pandas as pd\n#     import numpy as np\n\n\n# ***** DO NOT EDIT LINES BELOW *****\n# These lines may be overwritten if component details or inputs/outputs change."\n@register(\n    inputs={},\n    outputs={},\n    component_name="component 2",\n    description="description of component 2",\n    category="category",\n    uuid="'
    + str(get_uuid_from_seed("component 2"))
    + '",\n    group_id="'
    + str(get_uuid_from_seed("group of component 2"))
    + '",\n    tag="1.0.0"\n)\ndef main(*):\n    # entrypoint function for this component\n    # ***** DO NOT EDIT LINES ABOVE *****\n    # write your function code here.\n    # new comment\n    pass\n',
}

dto_json_wiring = {
    "id": "2634db74-157b-4c07-a49d-6aedc6f9a7bc",
    "name": "STANDARD-WIRING",
    "inputWirings": [
        {
            "id": "5021c197-3c38-4e66-b4dc-20e6b5a75bdc",
            "workflowInputName": "new_input",
            "adapterId": "direct_provisioning",
            "filters": {"value": 100},
        },
    ],
    "outputWirings": [],
}

valid_component_dto_dict = {
    "category": "Arithmetic",
    "code": 'from hetdesrun.component.registration import register\nfrom hetdesrun.datatypes import DataType\n\nimport pandas as pd\nimport numpy as np\n\n# ***** DO NOT EDIT LINES BELOW *****\n# These lines may be overwritten if component details or inputs/outputs change.\n@register(\n    inputs={"a": DataType.Any, "b": DataType.Integer},\n    outputs={"modulo": DataType.Any},\n    component_name="Modulo",\n    description="Calculates the modulo to some given b",\n    category="Arithmetic",\n    uuid="ebb5b2d1-7c25-94dd-ca81-6a9e5b21bc2f",\n    group_id="ebb5b2d1-7c25-94dd-ca81-6a9e5b21bc2f",\n    tag="1.0.0"\n)\ndef main(*, a, b):\n    # entrypoint function for this component\n    # ***** DO NOT EDIT LINES ABOVE *****\n    # write your function code here.\n\n    return {"modulo": a % b}\n',
    "description": "Calculates the modulo to some given b",
    "groupId": "ebb5b2d1-7c25-94dd-ca81-6a9e5b21bc2f",
    "id": "ebb5b2d1-7c25-94dd-ca81-6a9e5b21bc2f",
    "inputs": [
        {
            "id": "1aa579e3-e568-326c-0768-72c725844828",
            "name": "a",
            "posX": 0,
            "posY": 0,
            "type": "ANY",
        },
        {
            "id": "6198074e-18fa-0ba1-13a7-8d77b7f2c8f3",
            "name": "b",
            "posX": 0,
            "posY": 0,
            "type": "INT",
        },
    ],
    "name": "Modulo",
    "outputs": [
        {
            "id": "f309d0e5-6f20-2edb-c7be-13f84882af93",
            "name": "modulo",
            "posX": 0,
            "posY": 0,
            "type": "ANY",
        }
    ],
    "state": "RELEASED",
    "tag": "1.0.0",
    "type": "COMPONENT",
    "wirings": [
        {
            "id": "8e7d06f4-1085-4243-bff7-18991d377923",
            "name": "STANDARD-WIRING",
            "inputWirings": [
                {
                    "id": "77886042-28e9-4640-9405-9c3d1d61a08c",
                    "workflowInputName": "a",
                    "adapterId": "direct_provisioning",
                    "filters": {"value": "27"},
                },
                {
                    "id": "f64e6718-2d15-4c1a-828f-65da48fe56a2",
                    "workflowInputName": "b",
                    "adapterId": "direct_provisioning",
                    "filters": {"value": "4"},
                },
            ],
            "outputWirings": [],
        }
    ],
}


@pytest.mark.asyncio
async def test_get_component_revision_by_id_with_valid_component(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        store_single_transformation_revision(
            ComponentRevisionFrontendDto(
                **dto_json_component_1
            ).to_transformation_revision()
        )

        async with async_test_client as ac:
            response = await ac.get(
                "/api/components/" + str(get_uuid_from_seed("component 1"))
            )
        assert response.status_code == 200
        assert response.json() == dto_json_component_1


@pytest.mark.asyncio
async def test_get_component_revision_by_id_with_inexistent_component(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        async with async_test_client as ac:
            response = await ac.get(
                "/api/components/" + str(get_uuid_from_seed("inexistent component"))
            )
        assert response.status_code == 404
        assert "Found no" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_transformation_revision_from_component_dto(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        async with async_test_client as ac:
            response = await ac.post("/api/components/", json=dto_json_component_1)

        assert response.status_code == 201
        assert response.json()["name"] == dto_json_component_1["name"]


@pytest.mark.asyncio
async def test_update_transformation_revision_from_component_dto(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        store_single_transformation_revision(
            ComponentRevisionFrontendDto(
                **dto_json_component_1
            ).to_transformation_revision()
        )

        async with async_test_client as ac:
            response = await ac.put(
                "/api/components/" + str(get_uuid_from_seed("component 1")),
                json=dto_json_component_1_update,
            )

        assert response.status_code == 201
        assert response.json()["name"] == "new name"
        assert response.json()["category"] == "Test"
        assert response.json()["inputs"][0]["id"] == str(
            get_uuid_from_seed("new input")
        )
        print(response.json()["code"])
        assert "new_input" in response.json()["code"]


@pytest.mark.asyncio
async def test_update_transformation_revision_from_non_existing_component_dto(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        async with async_test_client as ac:
            response = await ac.put(
                "/api/components/" + str(get_uuid_from_seed("component 1")),
                json=dto_json_component_1_update,
            )

        assert response.status_code == 201
        assert response.json()["name"] == "new name"
        assert response.json()["category"] == "Test"
        assert response.json()["inputs"][0]["id"] == str(
            get_uuid_from_seed("new input")
        )
        assert "new comment" in response.json()["code"]
        assert "revision_group_id" in response.json()["code"]


@pytest.mark.asyncio
async def test_update_transformation_revision_from_released_component_dto(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        store_single_transformation_revision(
            ComponentRevisionFrontendDto(
                **dto_json_component_2
            ).to_transformation_revision()
        )

        async with async_test_client as ac:
            response = await ac.put(
                "/api/components/" + str(get_uuid_from_seed("component 2")),
                json=dto_json_component_2_update,
            )

        assert response.status_code == 403


@pytest.mark.asyncio
async def test_deprecate_transformation_revision_from_component_dto(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        store_single_transformation_revision(
            ComponentRevisionFrontendDto(
                **dto_json_component_2
            ).to_transformation_revision()
        )

        async with async_test_client as ac:
            response = await ac.put(
                "/api/components/" + str(get_uuid_from_seed("component 2")),
                json=dto_json_component_2_deprecate,
            )

        assert response.status_code == 201
        assert response.json()["state"] == "DISABLED"
        assert response.json()["name"] != "new name"
        assert response.json()["category"] != "Test"
        assert len(response.json()["inputs"]) == 0
        assert "new comment" not in response.json()["code"]


@pytest.mark.asyncio
async def test_delete_transformation_revision_from_component_dto(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        store_single_transformation_revision(
            ComponentRevisionFrontendDto(
                **dto_json_component_1
            ).to_transformation_revision()
        )

        async with async_test_client as ac:
            response = await ac.delete(
                "/api/components/" + str(get_uuid_from_seed("component 1")),
            )

        assert response.status_code == 204


@pytest.mark.asyncio
async def test_set_test_wiring_for_component_dto(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):

        store_single_transformation_revision(
            ComponentRevisionFrontendDto(
                **dto_json_component_1_update
            ).to_transformation_revision()
        )

        async with async_test_client as ac:
            response = await ac.post(
                "/api/components/"
                + str(get_uuid_from_seed("component 1"))
                + "/wirings",
                json=dto_json_wiring,
            )

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_execute_for_component_dto(async_test_client, clean_test_db_engine):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):

        store_single_transformation_revision(
            ComponentRevisionFrontendDto(
                **valid_component_dto_dict
            ).to_transformation_revision()
        )

        async with async_test_client as ac:
            response = await ac.post(
                "/api/components/" + valid_component_dto_dict["id"] + "/execute",
                json=valid_component_dto_dict["wirings"][0],
            )

        assert response.status_code == 200
        assert "output_types_by_output_name" in response.json()


@pytest.mark.asyncio
async def test_execute_for_component_without_hetdesrun_imports(async_test_client, clean_test_db_engine):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):

        path = (
            "./tests/data/components/"
            "alerts-from-score_100_38f168ef-cb06-d89c-79b3-0cd823f32e9d"
            ".json"
        )
        component_tr_json = load_json(path)
        wiring_json = {
            "id":"38f168ef-cb06-d89c-79b3-0cd823f32e9d",
            "name":"STANDARD-WIRING",
            "inputWirings":[
                {
                    "id":"8c249f92-4b81-457e-9371-24204d6b373b",
                    "workflowInputName":"scores",
                    "adapterId":"direct_provisioning",
                    "filters":{
                        "value":(
                            "{\n"
                            "    \"2020-01-03T08:20:03.000Z\": 18.7,\n"
                            "    \"2020-01-01T01:15:27.000Z\": 42.2,\n"
                            "    \"2020-01-03T08:20:04.000Z\": 25.9\n"
                            "}"
                        )
                    }
                },
                {
                    "id":"0f0f97f7-1f5d-4f5d-be11-7c7b78d02129",
                    "workflowInputName":"threshold",
                    "adapterId":"direct_provisioning",
                    "filters":{
                        "value":"30"
                    }
                }
            ],
            "outputWirings":[]
        }

        tr = TransformationRevision(**component_tr_json)
        tr.content = update_code(tr.content, tr.to_component_info())
        assert "COMPONENT_INFO" in tr.content
        
        store_single_transformation_revision(tr)

        async with async_test_client as ac:
            response = await ac.post(
                "/api/components/" + component_tr_json["id"] + "/execute",
                json=wiring_json,
            )

        assert response.status_code == 200
        assert "output_types_by_output_name" in response.json()
