from unittest import mock

import pytest

from hetdesrun.backend.models.transformation import TransformationRevisionFrontendDto
from hetdesrun.persistence import get_db_engine, sessionmaker
from hetdesrun.persistence.dbmodels import Base
from hetdesrun.persistence.dbservice.revision import (
    store_single_transformation_revision,
)
from hetdesrun.utils import get_uuid_from_seed


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


tr_dto_json_component_1 = {
    "id": str(get_uuid_from_seed("component 1")),
    "groupId": str(get_uuid_from_seed("group of component 1")),
    "name": "component 0",
    "description": "description of component 0",
    "category": "category",
    "type": "COMPONENT",
    "state": "DRAFT",
    "tag": "1.0.0",
    "inputs": [],
    "outputs": [],
    "wirings": [],
}
tr_dto_json_component_1_update = {
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
}
tr_dto_json_component_2 = {
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
}
tr_dto_json_component_2_update = {
    "id": str(get_uuid_from_seed("component 2")),
    "groupId": str(get_uuid_from_seed("group of component 2")),
    "name": "new name",
    "description": "description of component 2",
    "category": "category",
    "type": "COMPONENT",
    "state": "RELEASED",
    "tag": "1.0.0",
    "inputs": [],
    "outputs": [],
    "wirings": [],
}
tr_dto_json_component_2_deprecate = {
    "id": str(get_uuid_from_seed("component 2")),
    "groupId": str(get_uuid_from_seed("group of component 2")),
    "name": "new name",
    "description": "description of component 2",
    "category": "category",
    "type": "COMPONENT",
    "state": "DISABLED",
    "tag": "1.0.0",
    "inputs": [],
    "outputs": [],
    "wirings": [],
}
tr_dto_json_workflow_1 = {
    "id": str(get_uuid_from_seed("workflow 1")),
    "groupId": str(get_uuid_from_seed("group of workflow 1")),
    "name": "workflow 1",
    "description": "description of workflow 1",
    "category": "category",
    "type": "WORKFLOW",
    "state": "DRAFT",
    "tag": "1.0.0",
    "inputs": [],
    "outputs": [],
    "wirings": [],
}
tr_dto_json_workflow_2 = {
    "id": str(get_uuid_from_seed("workflow 2")),
    "groupId": str(get_uuid_from_seed("group of workflow 2")),
    "name": "workflow 2",
    "description": "description of workflow 2",
    "category": "category",
    "type": "WORKFLOW",
    "state": "DRAFT",
    "tag": "1.0.0",
    "inputs": [],
    "outputs": [],
    "wirings": [],
}


@pytest.mark.asyncio
async def test_get_all_base_items_with_valid_db_entries(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        store_single_transformation_revision(
            TransformationRevisionFrontendDto(
                **tr_dto_json_component_1
            ).to_transformation_revision()
        )
        store_single_transformation_revision(
            TransformationRevisionFrontendDto(
                **tr_dto_json_workflow_1
            ).to_transformation_revision()
        )
        store_single_transformation_revision(
            TransformationRevisionFrontendDto(
                **tr_dto_json_workflow_2
            ).to_transformation_revision()
        )

        async with async_test_client as ac:
            response = await ac.get("/api/base-items/")

        assert response.status_code == 200
        assert response.json()[0] == tr_dto_json_component_1
        assert response.json()[1] == tr_dto_json_workflow_1
        assert response.json()[2] == tr_dto_json_workflow_2


@pytest.mark.asyncio
async def test_get_all_base_items_with_specified_state(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        store_single_transformation_revision(
            TransformationRevisionFrontendDto(
                **tr_dto_json_component_1  # DRAFT
            ).to_transformation_revision()
        )
        store_single_transformation_revision(
            TransformationRevisionFrontendDto(
                **tr_dto_json_component_2  # RELEASED
            ).to_transformation_revision()
        )
        store_single_transformation_revision(
            TransformationRevisionFrontendDto(
                **tr_dto_json_workflow_1  # DRAFT
            ).to_transformation_revision()
        )
        tr_workflow_2 = TransformationRevisionFrontendDto(
            **tr_dto_json_workflow_2
        ).to_transformation_revision()
        tr_workflow_2.deprecate()
        store_single_transformation_revision(tr_workflow_2)

        async with async_test_client as ac:
            response_draft = await ac.get("/api/base-items/?state=DRAFT")
            response_released = await ac.get("/api/base-items/?state=RELEASED")
            response_disabled = await ac.get("/api/base-items/?state=DISABLED")
            response_foo = await ac.get("/api/base-items/?state=foo")

        assert response_draft.status_code == 200
        assert len(response_draft.json()) == 2
        assert response_draft.json()[0] == tr_dto_json_component_1
        assert response_draft.json()[1] == tr_dto_json_workflow_1
        assert response_released.status_code == 200
        assert len(response_released.json()) == 1
        assert response_released.json()[0] == tr_dto_json_component_2
        assert response_disabled.status_code == 200
        assert len(response_disabled.json()) == 1
        assert response_disabled.json()[0]["id"] == tr_dto_json_workflow_2["id"]
        assert response_disabled.json()[0]["state"] == "DISABLED"
        assert response_foo.status_code == 422
        assert (
            "not a valid enumeration member" in response_foo.json()["detail"][0]["msg"]
        )


@pytest.mark.asyncio
async def test_get_all_base_items_with_specified_type(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        store_single_transformation_revision(
            TransformationRevisionFrontendDto(
                **tr_dto_json_component_1  # DRAFT
            ).to_transformation_revision()
        )
        store_single_transformation_revision(
            TransformationRevisionFrontendDto(
                **tr_dto_json_component_2  # RELEASED
            ).to_transformation_revision()
        )
        store_single_transformation_revision(
            TransformationRevisionFrontendDto(
                **tr_dto_json_workflow_1  # DRAFT
            ).to_transformation_revision()
        )
        store_single_transformation_revision(
            TransformationRevisionFrontendDto(
                **tr_dto_json_workflow_2  # DRAFT
            ).to_transformation_revision()
        )

        async with async_test_client as ac:
            response_component = await ac.get("/api/base-items/?type=COMPONENT")
            response_workflow = await ac.get("/api/base-items/?type=WORKFLOW")
            response_foo = await ac.get("/api/base-items/?type=foo")

        assert response_component.status_code == 200
        assert len(response_component.json()) == 2
        assert response_component.json()[0] == tr_dto_json_component_1
        assert response_component.json()[1] == tr_dto_json_component_2
        assert response_workflow.status_code == 200
        assert len(response_workflow.json()) == 2
        assert response_workflow.json()[0] == tr_dto_json_workflow_1
        assert response_workflow.json()[1] == tr_dto_json_workflow_2
        assert response_foo.status_code == 422
        assert (
            "not a valid enumeration member" in response_foo.json()["detail"][0]["msg"]
        )


@pytest.mark.asyncio
async def test_get_all_base_items_with_specified_type_and_state(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        store_single_transformation_revision(
            TransformationRevisionFrontendDto(
                **tr_dto_json_component_1  # DRAFT
            ).to_transformation_revision()
        )
        store_single_transformation_revision(
            TransformationRevisionFrontendDto(
                **tr_dto_json_component_2  # RELEASED
            ).to_transformation_revision()
        )
        store_single_transformation_revision(
            TransformationRevisionFrontendDto(
                **tr_dto_json_workflow_1  # DRAFT
            ).to_transformation_revision()
        )
        store_single_transformation_revision(
            TransformationRevisionFrontendDto(
                **tr_dto_json_workflow_2  # DRAFT
            ).to_transformation_revision()
        )

        async with async_test_client as ac:
            response_released_component = await ac.get(
                "/api/base-items/?type=COMPONENT&state=RELEASED"
            )
            response_draft_workflow = await ac.get(
                "/api/base-items/?type=WORKFLOW&state=DRAFT"
            )

        assert response_released_component.status_code == 200
        assert len(response_released_component.json()) == 1
        assert response_released_component.json()[0] == tr_dto_json_component_2
        assert response_draft_workflow.status_code == 200
        assert len(response_draft_workflow.json()) == 2
        assert response_draft_workflow.json()[0] == tr_dto_json_workflow_1
        assert response_draft_workflow.json()[1] == tr_dto_json_workflow_2


@pytest.mark.asyncio
async def test_get_transformation_revision_by_id_with_component(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        store_single_transformation_revision(
            TransformationRevisionFrontendDto(
                **tr_dto_json_component_1
            ).to_transformation_revision()
        )

        async with async_test_client as ac:
            response = await ac.get(
                "/api/base-items/" + str(get_uuid_from_seed("component 1"))
            )
        assert response.status_code == 200
        assert response.json() == tr_dto_json_component_1


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
                "/api/base-items/"
                + str(get_uuid_from_seed("inexistent transformation revision"))
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
            TransformationRevisionFrontendDto(
                **tr_dto_json_workflow_1
            ).to_transformation_revision()
        )

        async with async_test_client as ac:
            response = await ac.get(
                "/api/base-items/" + str(get_uuid_from_seed("workflow 1"))
            )
        assert response.status_code == 200
        assert response.json() == tr_dto_json_workflow_1


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
                "/api/base-items/" + str(get_uuid_from_seed("inexistent workflow"))
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
            response = await ac.post("/api/base-items/", json=tr_dto_json_workflow_1)

        assert response.status_code == 201
        assert response.json()["name"] == tr_dto_json_workflow_1["name"]


@pytest.mark.asyncio
async def test_update_transformation_revision_with_component(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        store_single_transformation_revision(
            TransformationRevisionFrontendDto(
                **tr_dto_json_component_1
            ).to_transformation_revision()
        )

        async with async_test_client as ac:
            response = await ac.put(
                "/api/base-items/" + str(get_uuid_from_seed("component 1")),
                json=tr_dto_json_component_1_update,
            )

        assert response.status_code == 201
        assert response.json()["name"] == "new name"
        assert response.json()["category"] == "Test"
        assert response.json()["inputs"][0]["id"] == str(
            get_uuid_from_seed("new input")
        )


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
                "/api/base-items/" + str(get_uuid_from_seed("component 1")),
                json=tr_dto_json_component_1_update,
            )

        assert response.status_code == 201
        assert response.json()["name"] == "new name"
        assert response.json()["category"] == "Test"
        assert response.json()["inputs"][0]["id"] == str(
            get_uuid_from_seed("new input")
        )


@pytest.mark.asyncio
async def test_update_transformation_revision_from_released_component_dto(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        store_single_transformation_revision(
            TransformationRevisionFrontendDto(
                **tr_dto_json_component_2
            ).to_transformation_revision()
        )

        async with async_test_client as ac:
            response = await ac.put(
                "/api/base-items/" + str(get_uuid_from_seed("component 2")),
                json=tr_dto_json_component_2_update,
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
            TransformationRevisionFrontendDto(
                **tr_dto_json_component_2
            ).to_transformation_revision()
        )

        async with async_test_client as ac:
            response = await ac.put(
                "/api/base-items/" + str(get_uuid_from_seed("component 2")),
                json=tr_dto_json_component_2_deprecate,
            )

        assert response.status_code == 201
        assert response.json()["state"] == "DISABLED"
        assert response.json()["name"] != "new name"
        assert response.json()["category"] != "Test"
        assert len(response.json()["inputs"]) == 0
