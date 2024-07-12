import pytest

from hetdesrun.webservice.auth_dependency import get_auth_headers

# OFF


@pytest.mark.asyncio
async def test_external_auth_off_no_auth_headers(outgoing_auth_external_mode_off):
    assert await get_auth_headers(external=True) == {}


@pytest.mark.asyncio
async def test_internal_auth_off_no_auth_headers(outgoing_auth_internal_mode_off):
    assert await get_auth_headers(external=False) == {}


# FORWARD_OR_FIXED


@pytest.mark.asyncio
async def test_auth_external_forward_with_set_explicit_bearer_token(
    outgoing_auth_external_mode_forward_or_fixed,
    unset_request_auth_context,
    auth_bearer_token_for_outgoing_requests_is_set,
):
    assert await get_auth_headers(external=True) == {"Authorization": "Bearer some token string"}


@pytest.mark.asyncio
async def test_auth_external_forward_without_explicit_bearer_token(
    outgoing_auth_external_mode_forward_or_fixed,
    unset_request_auth_context,
    auth_bearer_token_for_outgoing_requests_not_set,
):
    # empty, since there is no request context
    assert await get_auth_headers(external=True) == {}


@pytest.mark.asyncio
async def test_auth_external_forward_from_request(
    outgoing_auth_external_mode_forward_or_fixed,
    set_request_auth_context,
):
    assert await get_auth_headers(external=True) == {"Authorization": "Bearer token from request"}


@pytest.mark.asyncio
async def test_auth_internal_forward_with_set_explicit_bearer_token(
    outgoing_auth_internal_mode_forward_or_fixed,
    unset_request_auth_context,
    auth_bearer_token_for_outgoing_requests_is_set,
):
    assert await get_auth_headers(external=False) == {"Authorization": "Bearer some token string"}


@pytest.mark.asyncio
async def test_auth_internal_forward_without_explicit_bearer_token(
    outgoing_auth_internal_mode_forward_or_fixed,
    unset_request_auth_context,
    auth_bearer_token_for_outgoing_requests_not_set,
):
    # empty, since there is no request context
    assert await get_auth_headers(external=False) == {}


@pytest.mark.asyncio
async def test_auth_internal_forward_from_request(
    outgoing_auth_internal_mode_forward_or_fixed,
    set_request_auth_context,
):
    assert await get_auth_headers(external=False) == {"Authorization": "Bearer token from request"}


# CLIENT


@pytest.mark.asyncio
async def test_auth_external_client_mode(
    outgoing_auth_external_mode_client, set_external_client_creds, mocked_token_request
):
    auth_header_dict = await get_auth_headers(external=True)
    assert len(auth_header_dict) == 1
    assert auth_header_dict["Authorization"].startswith("Bearer ")
    assert len(auth_header_dict["Authorization"]) > 30


@pytest.mark.asyncio
async def test_authinternal_client_mode(
    outgoing_auth_internal_mode_client,
    set_internal_client_creds,
    mocked_token_request,
):
    auth_header_dict = await get_auth_headers(external=False)
    assert len(auth_header_dict) == 1
    assert auth_header_dict["Authorization"].startswith("Bearer ")
    assert len(auth_header_dict["Authorization"]) > 30
