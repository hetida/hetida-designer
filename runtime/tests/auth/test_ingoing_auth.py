import asyncio
from unittest import mock

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
    auth_headers = await get_auth_headers()
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

        auth_headers_before_request = await get_auth_headers()
        assert len(auth_headers_before_request) == 0

        response = await client.get(
            "/api/transformations/",
            headers={"Authorization": "Bearer " + access_token},
        )
        assert response.status_code == 200

        auth_headers_after_response = await get_auth_headers()

        assert len(auth_headers_after_response) > 0
        assert auth_headers_after_response["Authorization"].startswith("Bearer ")
        return auth_headers_after_response

    first_1, second_1 = await asyncio.gather(
        request_task(0, valid_access_token),
        request_task(0.05, second_valid_access_token),
    )
    assert first_1["Authorization"] != second_1["Authorization"]

    first_2, second_2 = await asyncio.gather(
        request_task(0.05, valid_access_token),
        request_task(0, second_valid_access_token),
    )
    assert first_2["Authorization"] != second_2["Authorization"]

    assert first_1 == first_2
    assert second_1 == second_2

    # not leaked: after all tasks completed, the context var should be set back to its
    # default which leads to empty auth headers.
    last_auth_headers = await get_auth_headers()
    assert len(last_auth_headers) == 0


@pytest.mark.asyncio
async def test_auth_with_wrong_key_access_token_fails(
    open_async_test_client_with_auth,
    mocked_clean_test_db_session,
    wrong_key_access_token,
    mocked_pre_loaded_public_key,
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
    assert mocked_public_key_fetching.called == 2


@pytest.mark.asyncio
async def test_auth_without_access_token_fails(
    open_async_test_client_with_auth,
    mocked_clean_test_db_session,
    mocked_public_key_fetching,
):
    client = open_async_test_client_with_auth
    response = await client.get("/api/transformations/", headers={})
    assert response.status_code == 401
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


@pytest.mark.asyncio
async def test_auth_role_checking_works(
    open_async_test_client_with_auth,
    mocked_clean_test_db_session,
    valid_access_token_with_role,  # has "some_roles": ["allowed_hd_user"] in payload
    mocked_public_key_fetching,
):
    client = open_async_test_client_with_auth

    # default: no role checks. Should work!
    response = await client.get(
        "/api/transformations/",
        headers={"Authorization": "Bearer " + valid_access_token_with_role},
    )
    assert response.status_code == 200
    auth_headers = await get_auth_headers()
    assert len(auth_headers) > 0
    assert auth_headers["Authorization"].startswith("Bearer ")

    # activate role checks
    with (
        mock.patch("hetdesrun.webservice.config.runtime_config.auth_role_key", "some_roles"),
        mock.patch(
            "hetdesrun.webservice.config.runtime_config.auth_allowed_role", "allowed_hd_user"
        ),
    ):
        # request with correct access token succeeds
        response = await client.get(
            "/api/transformations/",
            headers={"Authorization": "Bearer " + valid_access_token_with_role},
        )
        assert response.status_code == 200
        auth_headers = await get_auth_headers()
        assert len(auth_headers) > 0
        assert auth_headers["Authorization"].startswith("Bearer ")

    # role expected in other key should yield 403
    with (
        mock.patch("hetdesrun.webservice.config.runtime_config.auth_role_key", "other_roles"),
        mock.patch(
            "hetdesrun.webservice.config.runtime_config.auth_allowed_role", "allowed_hd_user"
        ),
    ):
        # request with correct access token succeeds
        response = await client.get(
            "/api/transformations/",
            headers={"Authorization": "Bearer " + valid_access_token_with_role},
        )
        assert response.status_code == 403

    # role not allowed should yield 403
    with (
        mock.patch("hetdesrun.webservice.config.runtime_config.auth_role_key", "some_roles"),
        mock.patch(
            "hetdesrun.webservice.config.runtime_config.auth_allowed_role", "not_allowed_hd_user"
        ),
    ):
        # request with correct access token succeeds
        response = await client.get(
            "/api/transformations/",
            headers={"Authorization": "Bearer " + valid_access_token_with_role},
        )
        assert response.status_code == 403

    # role not set (deactivating role checking), but roles present should yield 200
    with (
        mock.patch("hetdesrun.webservice.config.runtime_config.auth_role_key", "some_roles"),
        mock.patch("hetdesrun.webservice.config.runtime_config.auth_allowed_role", None),
    ):
        # request with correct access token succeeds
        response = await client.get(
            "/api/transformations/",
            headers={"Authorization": "Bearer " + valid_access_token_with_role},
        )
        assert response.status_code == 200
        auth_headers = await get_auth_headers()
        assert len(auth_headers) > 0
        assert auth_headers["Authorization"].startswith("Bearer ")


@pytest.mark.asyncio
async def test_auth_rejects_token_without_exp(
    open_async_test_client_with_auth,
    mocked_clean_test_db_session,
    access_token_without_exp,
    mocked_public_key_fetching,
):
    """A signed token without an exp claim must be rejected: tokens must carry an
    expiration so that they cannot be valid indefinitely.
    """
    client = open_async_test_client_with_auth
    response = await client.get(
        "/api/transformations/",
        headers={"Authorization": "Bearer " + access_token_without_exp},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_role_checking_rejects_non_list_role_claim(
    open_async_test_client_with_auth,
    mocked_clean_test_db_session,
    valid_access_token_with_string_role,  # has "some_roles": "superallowed_hd_user_x"
    mocked_public_key_fetching,
):
    """The role claim must be a JSON array.

    A string role claim must not grant access even when it contains the allowed role
    as a substring: membership is checked against a list, not via substring matching.
    """
    client = open_async_test_client_with_auth

    with (
        mock.patch("hetdesrun.webservice.config.runtime_config.auth_role_key", "some_roles"),
        mock.patch(
            "hetdesrun.webservice.config.runtime_config.auth_allowed_role", "allowed_hd_user"
        ),
    ):
        response = await client.get(
            "/api/transformations/",
            headers={"Authorization": "Bearer " + valid_access_token_with_string_role},
        )
        assert response.status_code == 403
