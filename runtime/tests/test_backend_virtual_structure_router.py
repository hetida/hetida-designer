import json
from unittest import mock

import pytest
from pydantic import SecretStr
from sqlalchemy.future.engine import Engine

from hetdesrun.persistence.db_engine_and_session import sessionmaker
from hetdesrun.persistence.structure_service_dbmodels import Base as structure_service_Base


@pytest.fixture()
def clean_test_db_engine_for_vst_router(test_db_engine: Engine) -> Engine:
    structure_service_Base.metadata.drop_all(test_db_engine)
    structure_service_Base.metadata.create_all(test_db_engine)
    return test_db_engine


@pytest.fixture()
def mocked_clean_test_db_session_for_vst_router(clean_test_db_engine_for_vst_router):
    with mock.patch(
        "hetdesrun.persistence.db_engine_and_session.Session",
        sessionmaker(clean_test_db_engine_for_vst_router),
    ) as _fixture:
        yield _fixture


@pytest.fixture()
def maintenance_secret_set_for_vst_router():
    with mock.patch(
        "hetdesrun.webservice.config.runtime_config.maintenance_secret",
        SecretStr("testsecret"),
    ) as _fixture:
        yield _fixture


@pytest.mark.asyncio
async def test_update_structure(
    async_test_client,
    mocked_clean_test_db_session_for_vst_router,
    maintenance_secret_set_for_vst_router,
):
    file_path = "tests/virtual_structure_adapter/data/simple_end_to_end_test.json"
    with open(file_path) as file:
        structure_json = json.load(file)
    maintenance_payload = {"maintenance_payload": {"maintenance_secret": "testsecret"}}

    async with async_test_client as ac:
        response = await ac.put(
            "/api/structure/update/",
            json={**maintenance_payload, "new_structure": structure_json},
        )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_update_structure_with_formally_invalid_structure(
    async_test_client,
    mocked_clean_test_db_session_for_vst_router,
    maintenance_secret_set_for_vst_router,
):
    maintenance_payload = {"maintenance_payload": {"maintenance_secret": "testsecret"}}
    async with async_test_client as ac:
        response = await ac.put(
            "/api/structure/update/", json={**maintenance_payload, "new_structure": "'nf'"}
        )
    assert response.status_code == 422, f"Unexpected status code: {response.status_code}"
    assert "value is not a valid dict" in response.json()["detail"][0]["msg"]


@pytest.mark.asyncio
async def test_update_structure_with_invalid_structure(
    async_test_client,
    mocked_clean_test_db_session_for_vst_router,
    maintenance_secret_set_for_vst_router,
):
    json_with_type_mismatch = {
        "element_types": [
            {
                "external_id": "Waterworks_Type",
                "stakeholder_key": "GW",
                "name": [42],  # Wrong datatype
                "description": "Element type for waterworks",
            }
        ]
    }
    maintenance_payload = {"maintenance_payload": {"maintenance_secret": "testsecret"}}

    async with async_test_client as ac:
        response = await ac.put(
            "/api/structure/update/",
            json={**maintenance_payload, "new_structure": json_with_type_mismatch},
        )
    assert response.status_code == 422, f"Unexpected status code: {response.status_code}"
    assert "str type expected" in response.json()["detail"][0]["msg"]


@pytest.mark.asyncio
async def test_update_structure_with_logically_invalid_structure(
    async_test_client,
    mocked_clean_test_db_session_for_vst_router,
    maintenance_secret_set_for_vst_router,
):
    file_path = "tests/structure/data/db_test_invalid_structure_no_duplicate_id.json"
    with open(file_path) as file:
        structure_json = json.load(file)
    maintenance_payload = {"maintenance_payload": {"maintenance_secret": "testsecret"}}

    async with async_test_client as ac:
        response = await ac.put(
            "/api/structure/update/", json={**maintenance_payload, "new_structure": structure_json}
        )
    assert response.status_code == 422, f"Unexpected status code: {response.status_code}"
    assert "The stakeholder key and external id pair" in response.json()["detail"][0]["msg"]


@pytest.mark.asyncio
async def test_update_structure_with_false_maintenance_payload(
    async_test_client,
    mocked_clean_test_db_session_for_vst_router,
    maintenance_secret_set_for_vst_router,
):
    file_path = "tests/virtual_structure_adapter/data/simple_end_to_end_test.json"
    with open(file_path) as file:
        structure_json = json.load(file)
    maintenance_payload = {"maintenance_payload": {"maintenance_secret": "nf"}}

    async with async_test_client as ac:
        response = await ac.put(
            "/api/structure/update/", json={**maintenance_payload, "new_structure": structure_json}
        )
    assert response.status_code == 403, f"Unexpected status code: {response.status_code}"
    assert "maintenance secret check failed" in response.json()["detail"]["authorization_error"]
