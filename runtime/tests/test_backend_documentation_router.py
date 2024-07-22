import json

import pytest

from hetdesrun.backend.models.info import DocumentationFrontendDto
from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.persistence import get_db_engine
from hetdesrun.persistence.dbmodels import Base
from hetdesrun.persistence.dbservice.revision import (
    store_single_transformation_revision,
)
from hetdesrun.persistence.models.io import IOInterface
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.utils import State, Type, get_uuid_from_seed


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


component_tr_1 = TransformationRevision(
    id=get_uuid_from_seed("component 1"),
    revision_group_id=get_uuid_from_seed("group of component 1"),
    name="component 0",
    description="description of component 0",
    category="category",
    type=Type.COMPONENT,
    state=State.DRAFT,
    version_tag="1.0.0",
    io_interface=IOInterface(),
    documentation="documentation",
    content="code",
    test_wiring=WorkflowWiring(),
)


@pytest.mark.asyncio
async def test_get_documentation(async_test_client, mocked_clean_test_db_session):
    store_single_transformation_revision(component_tr_1)

    async with async_test_client as ac:
        response = await ac.get("/api/documentations/" + str(get_uuid_from_seed("component 1")))
    assert response.status_code == 200
    assert response.json()["document"] == "documentation"


@pytest.mark.asyncio
async def test_get_documentation_of_inexistent_component(
    async_test_client, mocked_clean_test_db_session
):
    async with async_test_client as ac:
        response = await ac.get(
            "/api/documentations/" + str(get_uuid_from_seed("inexistent component"))
        )
    assert response.status_code == 404
    assert "Found no" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_documentation_of_component_dto_with_unmatching_ids(
    async_test_client, mocked_clean_test_db_session
):
    store_single_transformation_revision(component_tr_1)

    new_documentation = DocumentationFrontendDto(
        id=get_uuid_from_seed("documentation"), document="new documentation"
    )

    json_of_new_documentation = json.loads(new_documentation.json(by_alias=True))

    async with async_test_client as ac:
        response = await ac.put(
            "/api/documentations/" + str(get_uuid_from_seed("component 1")),
            json=json_of_new_documentation,
        )

    assert response.status_code == 409
    assert "does not match" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_documentation_of_component_dto(
    async_test_client, mocked_clean_test_db_session
):
    store_single_transformation_revision(component_tr_1)

    new_documentation = DocumentationFrontendDto(
        id=get_uuid_from_seed("component 1"), document="new documentation"
    )

    json_of_new_documentation = json.loads(new_documentation.json(by_alias=True))

    async with async_test_client as ac:
        response = await ac.put(
            "/api/documentations/" + str(get_uuid_from_seed("component 1")),
            json=json_of_new_documentation,
        )

    assert response.status_code == 201
    assert response.json() == json_of_new_documentation


@pytest.mark.asyncio
async def test_delete_documentation_of_component_dto(
    async_test_client, mocked_clean_test_db_session
):
    store_single_transformation_revision(component_tr_1)

    async with async_test_client as ac:
        response = await ac.delete(
            "/api/documentations/" + str(get_uuid_from_seed("component 1")),
        )

    assert response.status_code == 204
