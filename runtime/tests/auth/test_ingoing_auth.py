import pytest
from unittest import mock


@pytest.mark.asyncio
async def test_auth_with_correct_access_token(
    open_async_test_client_with_auth,
    mocked_clean_test_db_session,
    valid_access_token,
    mocked_pre_loaded_public_key,
):
    client = open_async_test_client_with_auth
    # request with correct access token succeeds
    response = await client.get(
        "/api/transformations/",
        headers={"Authorization": "Bearer " + valid_access_token},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_auth_with_wrong_key_access_token(
    open_async_test_client_with_auth,
    mocked_clean_test_db_session,
    wrong_key_access_token,
    mocked_pre_loaded_public_key,
):
    client = open_async_test_client_with_auth

    # request with correct access token succeeds
    response = await client.get(
        "/api/transformations/",
        headers={"Authorization": "Bearer " + wrong_key_access_token},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_without_access_token(
    open_async_test_client_with_auth,
    mocked_clean_test_db_session,
    mocked_pre_loaded_public_key,
):
    client = open_async_test_client_with_auth
    response = await client.get("/api/transformations/", headers={})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_info_endpoints_access_without_access_token(
    open_async_test_client_with_auth,
    mocked_clean_test_db_session,
    mocked_pre_loaded_public_key,
):
    """Test auth-free access to endpoints for liveness probing"""
    client = open_async_test_client_with_auth
    response = await client.get("/api/info/", headers={})
    assert response.status_code == 200

    response = await client.get("/engine/info", headers={})
    assert response.status_code == 200

    response = await client.get("/adapters/localfile/info", headers={})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_auth_wrong_public_key(
    open_async_test_client_with_auth,
    mocked_clean_test_db_session,
    valid_access_token,
    mocked_pre_loaded_wrong_public_key,
):
    client = open_async_test_client_with_auth

    response = await client.get(
        "/api/transformations/",
        headers={"Authorization": "Bearer " + valid_access_token},
    )
    assert response.status_code == 401
