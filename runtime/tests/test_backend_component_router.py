from unittest import mock
import pytest

from starlette.testclient import TestClient

from hetdesrun.webservice.application import app

from hetdesrun.persistence import get_db_engine, sessionmaker

from hetdesrun.persistence.dbmodels import Base
from hetdesrun.persistence.dbservice.revision import (
    store_single_transformation_revision,
)

from hetdesrun.utils import get_uuid_from_seed

from hetdesrun.backend.models.component import ComponentRevisionFrontendDto

from hetdesrun.exportimport.importing import load_json


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

valid_component_dto_dict = load_json(
    "./transformations/components/arithmetic/modulo_100_ebb5b2d1-7c25-94dd-ca81-6a9e5b21bc2f.json"
)


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
        assert "uuid" in response.json()["code"]


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
