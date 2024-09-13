import json

import pytest


@pytest.mark.asyncio
async def test_update_structure(async_test_client, mocked_clean_test_db_session):
    file_path = "tests/virtual_structure_adapter/data/simple_end_to_end_test.json"
    with open(file_path) as file:
        structure_json = json.load(file)

    async with async_test_client as ac:
        response = await ac.put("/api/structure/update/", json=structure_json)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_update_structure_with_invalid_structure(
    async_test_client, mocked_clean_test_db_session
):
    file_path = "tests/structure/data/db_test_invalid_structure_no_duplicate_id.json"
    with open(file_path) as file:
        structure_json = json.load(file)

    async with async_test_client as ac:
        response = await ac.put("/api/structure/update/", json=structure_json)
    assert response.status_code == 500
    assert "Integrity Error while updating or inserting the structure" in response.json()["detail"]
