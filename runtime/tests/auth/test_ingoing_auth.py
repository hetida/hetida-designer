import asyncio

import pytest

from hetdesrun.webservice.auth_dependency import get_auth_headers


@pytest.mark.asyncio
async def test_auth_with_correct_access_token_works(
    open_async_test_client_with_auth,
    mocked_clean_test_db_session,
    valid_access_token,
    mocked_public_key_fetching,
):
    client = open_async_test_client_with_auth
    # request with correct access token succeeds
    response = await client.get(
        "/api/transformations/",
        headers={"Authorization": "Bearer " + valid_access_token},
    )
    assert response.status_code == 200
    auth_headers = get_auth_headers()
    assert len(auth_headers) > 0
    assert auth_headers["Authorization"].startswith("Bearer ")


@pytest.mark.asyncio
async def test_auth_headers_stored_correctly(
    open_async_test_client_with_auth,
    mocked_clean_test_db_session,
    valid_access_token,
    second_valid_access_token,
    mocked_public_key_fetching,
):
    """Test storage / separation of access token

    The access token is stored in a context var to be reused when making external
    requests to the runtime servide and adapters. This test tries to ensure that
    this indeed encloses the context var inside each request handling task and
    does not leak the access token across such tasks.
    """
    client = open_async_test_client_with_auth

    async def request_task(sleep_time_before, access_token):
        await asyncio.sleep(sleep_time_before)

        auth_headers_before_request = get_auth_headers()
        assert len(auth_headers_before_request) == 0

        response = await client.get(
            "/api/transformations/",
            headers={"Authorization": "Bearer " + access_token},
        )
        assert response.status_code == 200

        auth_headers_after_response = get_auth_headers()

        assert len(auth_headers_after_response) > 0
        assert auth_headers_after_response["Authorization"].startswith("Bearer ")
        return auth_headers_after_response

    first_1, second_1 = await asyncio.gather(
        request_task(0, valid_access_token), request_task(1, second_valid_access_token)
    )
    assert first_1["Authorization"] != second_1["Authorization"]

    first_2, second_2 = await asyncio.gather(
        request_task(1, valid_access_token), request_task(0, second_valid_access_token)
    )
    assert first_2["Authorization"] != second_2["Authorization"]

    assert first_1 == first_2
    assert second_1 == second_2

    # not leaked: after all tasks completed, the context var should be set back to its
    # default which leads to empty auth headers.
    last_auth_headers = get_auth_headers()
    assert len(last_auth_headers) == 0


@pytest.mark.asyncio
async def test_auth_with_wrong_key_access_token_fails(
    open_async_test_client_with_auth,
    mocked_clean_test_db_session,
    wrong_key_access_token,
    mocked_public_key_fetching,
):
    client = open_async_test_client_with_auth

    # request with correct access token succeeds
    response = await client.get(
        "/api/transformations/",
        headers={"Authorization": "Bearer " + wrong_key_access_token},
    )
    assert response.status_code == 401
    # should have tried exactly once to update the public key:
    assert mocked_public_key_fetching.called == 1


@pytest.mark.asyncio
async def test_auth_without_access_token_fails(
    open_async_test_client_with_auth,
    mocked_clean_test_db_session,
    mocked_public_key_fetching,
):
    client = open_async_test_client_with_auth
    response = await client.get("/api/transformations/", headers={})
    assert response.status_code == 403
    # empty auth header should fail before trying to update public key:
    assert mocked_public_key_fetching.called == 0


@pytest.mark.asyncio
async def test_info_endpoints_access_without_access_token_succeeds(
    open_async_test_client_with_auth,
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
async def test_auth_wrong_public_key_fails(
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
