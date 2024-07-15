import datetime
from copy import deepcopy
from json import JSONDecodeError
from unittest import mock
from uuid import uuid4

import pytest
from httpx import HTTPError

from hetdesrun.webservice.auth_outgoing import (
    ClientCredentialsGrantCredentials,
    PasswordGrantCredentials,
    ServiceAuthenticationError,
    ServiceCredentials,
    TokenResponse,
    create_or_get_named_access_token_manager,
    obtain_or_refresh_token,
    obtain_token_from_auth_provider,
    refresh_token_from_auth_provider,
)


@pytest.fixture()
def http_error_token_request():
    async def mocked_post_to_auth_provider(*args, **kwargs):
        mocked_post_to_auth_provider.last_called_args = deepcopy(args)
        mocked_post_to_auth_provider.last_called_kwargs = deepcopy(kwargs)
        raise HTTPError("test error")

    with mock.patch(
        "hetdesrun.webservice.auth_outgoing.post_to_auth_provider",
        mocked_post_to_auth_provider,
    ) as test_mocked_post_to_auth_provider:
        yield test_mocked_post_to_auth_provider


@pytest.fixture()
def json_parsing_error_token_request():
    mocked_resp = mock.Mock
    mocked_resp.json = mock.Mock(side_effect=JSONDecodeError("json parsing error", pos=0, doc="?"))
    mocked_resp.text = "not a json doc"

    async def mocked_post_to_auth_provider(*args, **kwargs):
        mocked_post_to_auth_provider.last_called_args = deepcopy(args)
        mocked_post_to_auth_provider.last_called_kwargs = deepcopy(kwargs)
        return mocked_resp

    with mock.patch(
        "hetdesrun.webservice.auth_outgoing.post_to_auth_provider",
        mocked_post_to_auth_provider,
    ) as test_mocked_post_to_auth_provider:
        yield test_mocked_post_to_auth_provider


@pytest.fixture()
def invalid_token_response_mocked_token_request(valid_token_response):
    mocked_resp = mock.Mock
    mocked_resp.json = mock.Mock(return_value={"a": 42})

    async def mocked_post_to_auth_provider(*args, **kwargs):
        mocked_post_to_auth_provider.last_called_args = deepcopy(args)
        mocked_post_to_auth_provider.last_called_kwargs = deepcopy(kwargs)
        return mocked_resp

    with mock.patch(
        "hetdesrun.webservice.auth_outgoing.post_to_auth_provider",
        mocked_post_to_auth_provider,
    ) as test_mocked_post_to_auth_provider:
        yield test_mocked_post_to_auth_provider


@pytest.mark.asyncio
async def test_outgoing_auth_token_fetching_with_password_grant(mocked_token_request):
    token_response = await obtain_token_from_auth_provider(
        ServiceCredentials(
            realm="my-realm",
            grant_credentials=PasswordGrantCredentials(
                client_id="my-client", username="user1", password="mYpAsSwOrD"
            ),
            auth_url="https://test.com/auth",
            post_client_kwargs={"verify": False},
        )
    )

    assert token_response == TokenResponse(
        issue_timestamp=token_response.issue_timestamp, **(mocked_token_request.token_response_dict)
    )

    assert mocked_token_request.last_called_kwargs == {
        "url": "https://test.com/auth/realms/my-realm/protocol/openid-connect/token",
        "data": {
            "grant_type": "password",
            "client_id": "my-client",
            "username": "user1",
            "password": "mYpAsSwOrD",
        },
        "async_client_kwargs": {"verify": False},
        "post_kwargs": {},
    }

    assert (
        datetime.datetime.now(datetime.timezone.utc) - token_response.issue_timestamp
    ).total_seconds() < 30


@pytest.mark.asyncio
async def test_http_error_on_outgoing_auth_token_fetching(
    http_error_token_request,
):
    with pytest.raises(ServiceAuthenticationError, match=r".*test error.*"):
        _token_response = await obtain_token_from_auth_provider(
            ServiceCredentials(
                realm="my-realm",
                grant_credentials=PasswordGrantCredentials(
                    client_id="my-client", username="user1", password="mYpAsSwOrD"
                ),
                auth_url="https://test.com/auth",
                post_client_kwargs={"verify": False},
            )
        )


@pytest.mark.asyncio
async def test_json_parsing_error_on_outgoing_auth_token_fetching(
    json_parsing_error_token_request,
):
    with pytest.raises(ServiceAuthenticationError, match=r".*json parsing error.*"):
        _token_response = await obtain_token_from_auth_provider(
            ServiceCredentials(
                realm="my-realm",
                grant_credentials=PasswordGrantCredentials(
                    client_id="my-client", username="user1", password="mYpAsSwOrD"
                ),
                auth_url="https://test.com/auth",
                post_client_kwargs={"verify": False},
            )
        )


@pytest.mark.asyncio
async def test_invalid_token_response_outgoing_auth_token_fetching(
    invalid_token_response_mocked_token_request,
):
    with pytest.raises(ServiceAuthenticationError, match=r".*validation error.*"):
        _token_response = await obtain_token_from_auth_provider(
            ServiceCredentials(
                realm="my-realm",
                grant_credentials=PasswordGrantCredentials(
                    client_id="my-client", username="user1", password="mYpAsSwOrD"
                ),
                auth_url="https://test.com/auth",
                post_client_kwargs={"verify": False},
            )
        )


@pytest.mark.asyncio
async def test_outgoing_auth_token_fetching_with_client_credentials_grant(
    mocked_token_request,
):
    token_response = await obtain_token_from_auth_provider(
        ServiceCredentials(
            realm="my-realm",
            grant_credentials=ClientCredentialsGrantCredentials(
                client_id="my-client", client_secret="abcd"
            ),
            auth_url="https://test.com/auth",
            post_client_kwargs={"verify": False},
        )
    )

    assert token_response == TokenResponse(
        issue_timestamp=token_response.issue_timestamp, **(mocked_token_request.token_response_dict)
    )

    assert mocked_token_request.last_called_kwargs == {
        "url": "https://test.com/auth/realms/my-realm/protocol/openid-connect/token",
        "data": {
            "grant_type": "client_credentials",
            "client_id": "my-client",
            "client_secret": "abcd",
        },
        "async_client_kwargs": {"verify": False},
        "post_kwargs": {},
    }

    assert (
        datetime.datetime.now(datetime.timezone.utc) - token_response.issue_timestamp
    ).total_seconds() < 30


@pytest.mark.asyncio
async def test_outgoing_auth_token_refreshing(
    mocked_token_request,
):
    token_response = await refresh_token_from_auth_provider(
        refresh_token="mock",
        service_user_credentials=ServiceCredentials(
            realm="my-realm",
            grant_credentials=ClientCredentialsGrantCredentials(
                client_id="my-client", client_secret="abcd"
            ),
            auth_url="https://test.com/auth",
            post_client_kwargs={"verify": False},
        ),
    )

    assert token_response == TokenResponse(
        issue_timestamp=token_response.issue_timestamp, **(mocked_token_request.token_response_dict)
    )

    assert mocked_token_request.last_called_kwargs == {
        "url": "https://test.com/auth/realms/my-realm/protocol/openid-connect/token",
        "data": {
            "refresh_token": "mock",
            "grant_type": "refresh_token",
            "client_id": "my-client",
        },
        "async_client_kwargs": {"verify": False},
        "post_kwargs": {},
    }

    assert (
        datetime.datetime.now(datetime.timezone.utc) - token_response.issue_timestamp
    ).total_seconds() < 30


@pytest.fixture()
def service_credentials():
    return ServiceCredentials(
        realm="my-realm",
        grant_credentials=ClientCredentialsGrantCredentials(
            client_id="my-client", client_secret="abcd"
        ),
        auth_url="https://test.com/auth",
        post_client_kwargs={"verify": False},
    )


@pytest.fixture()
def result_token_info() -> TokenResponse:
    return TokenResponse(
        access_token="result_access_token",
        refresh_token="result_refresh_token",
        expires_in=600,
        refresh_expires_in=600,
        token_type="bearer",
        not_before_policy=0,
        session_state="result session state",
        scope="result scope",
        issue_timestamp=datetime.datetime.now(datetime.timezone.utc),
    )


@pytest.fixture()
def token_info_both_longer_valid() -> TokenResponse:
    return TokenResponse(
        access_token="some_access_token",
        refresh_token="some_refresh_token",
        expires_in=600,
        refresh_expires_in=600,
        token_type="bearer",
        not_before_policy=0,
        session_state="some session state",
        scope="some scope",
        issue_timestamp=datetime.datetime.now(datetime.timezone.utc),
    )


@pytest.fixture()
def token_info_access_overdue_refresh_valid() -> TokenResponse:
    return TokenResponse(
        access_token="some_access_token",
        refresh_token="some_refresh_token",
        expires_in=-1,
        refresh_expires_in=600,
        token_type="bearer",
        not_before_policy=0,
        session_state="some session state",
        scope="some scope",
        issue_timestamp=datetime.datetime.now(datetime.timezone.utc),
    )


@pytest.fixture()
def token_info_access_valid_refresh_overdue() -> TokenResponse:
    return TokenResponse(
        access_token="some_access_token",
        refresh_token="some_refresh_token",
        expires_in=600,
        refresh_expires_in=-1,
        token_type="bearer",
        not_before_policy=0,
        session_state="some session state",
        scope="some scope",
        issue_timestamp=datetime.datetime.now(datetime.timezone.utc),
    )


@pytest.fixture()
def token_info_both_overdue() -> TokenResponse:
    return TokenResponse(
        access_token="some_access_token",
        refresh_token="some_refresh_token",
        expires_in=-1,
        refresh_expires_in=-1,
        token_type="bearer",
        not_before_policy=0,
        session_state="some session state",
        scope="some scope",
        issue_timestamp=datetime.datetime.now(datetime.timezone.utc),
    )


@pytest.fixture()
def obtain_token_works(result_token_info):
    async def mocked_obtain_func(*args, **kwargs):
        mocked_obtain_func.last_called_args = deepcopy(args)
        mocked_obtain_func.last_called_kwargs = deepcopy(kwargs)
        mocked_obtain_func.num_called += 1
        return result_token_info

    mocked_obtain_func.num_called = 0
    with mock.patch(
        "hetdesrun.webservice.auth_outgoing.obtain_token_from_auth_provider",
        mocked_obtain_func,
    ) as mocked:
        yield mocked


@pytest.fixture()
def obtain_token_raises():
    async def mocked_obtain_func(*args, **kwargs):
        mocked_obtain_func.last_called_args = deepcopy(args)
        mocked_obtain_func.last_called_kwargs = deepcopy(kwargs)
        mocked_obtain_func.num_called += 1
        raise ServiceAuthenticationError

    mocked_obtain_func.num_called = 0

    with mock.patch(
        "hetdesrun.webservice.auth_outgoing.obtain_token_from_auth_provider",
        mocked_obtain_func,
    ) as _mocked_obtain_token_function_raises:
        yield _mocked_obtain_token_function_raises


@pytest.fixture()
def refresh_token_works(result_token_info):
    async def mocked_obtain_func(*args, **kwargs):
        mocked_obtain_func.last_called_args = deepcopy(args)
        mocked_obtain_func.last_called_kwargs = deepcopy(kwargs)
        mocked_obtain_func.num_called += 1
        return result_token_info

    mocked_obtain_func.num_called = 0
    with mock.patch(
        "hetdesrun.webservice.auth_outgoing.refresh_token_from_auth_provider",
        mocked_obtain_func,
    ) as mocked:
        yield mocked


@pytest.fixture()
def refresh_token_raises():
    async def mocked_obtain_func(*args, **kwargs):
        mocked_obtain_func.last_called_args = deepcopy(args)
        mocked_obtain_func.last_called_kwargs = deepcopy(kwargs)
        mocked_obtain_func.num_called += 1
        raise ServiceAuthenticationError

    mocked_obtain_func.num_called = 0

    with mock.patch(
        "hetdesrun.webservice.auth_outgoing.refresh_token_from_auth_provider",
        mocked_obtain_func,
    ) as _mocked_obtain_token_function_raises:
        yield _mocked_obtain_token_function_raises


@pytest.mark.asyncio
async def test_obtain_refresh_logic_valid_existing_token(
    token_info_both_longer_valid,
    obtain_token_works,
    refresh_token_works,
    service_credentials,
):
    token_info = await obtain_or_refresh_token(
        service_user_credentials=service_credentials,
        existing_token_info=token_info_both_longer_valid,
    )

    # original token should be returned, since it is still valid enough:
    assert token_info == token_info_both_longer_valid

    # no token obtain or refresh:
    assert obtain_token_works.num_called == 0
    assert refresh_token_works.num_called == 0


@pytest.mark.asyncio
async def test_obtain_refresh_logic_new_token(
    obtain_token_works, refresh_token_works, service_credentials, result_token_info
):
    token_info = await obtain_or_refresh_token(
        service_user_credentials=service_credentials,
        existing_token_info=None,
    )

    assert token_info == result_token_info

    assert obtain_token_works.num_called == 1
    assert refresh_token_works.num_called == 0


@pytest.mark.asyncio
async def test_obtain_refresh_logic_refresh(
    token_info_access_overdue_refresh_valid,
    obtain_token_works,
    refresh_token_works,
    service_credentials,
    result_token_info,
):
    token_info = await obtain_or_refresh_token(
        service_user_credentials=service_credentials,
        existing_token_info=token_info_access_overdue_refresh_valid,
    )

    assert token_info == result_token_info

    assert obtain_token_works.num_called == 0
    assert refresh_token_works.num_called == 1


@pytest.mark.asyncio
async def test_obtain_refresh_logic_both_overdue(
    token_info_both_overdue,
    obtain_token_works,
    refresh_token_works,
    service_credentials,
    result_token_info,
):
    token_info = await obtain_or_refresh_token(
        service_user_credentials=service_credentials,
        existing_token_info=token_info_both_overdue,
    )

    # at the end a completely new token should be obtained

    # Mock returns None
    assert token_info == result_token_info

    assert obtain_token_works.num_called == 1
    assert refresh_token_works.num_called == 0


@pytest.mark.asyncio
async def test_obtain_refresh_logic_valid_existing_token_refresh_overdue(
    token_info_access_valid_refresh_overdue,
    obtain_token_works,
    refresh_token_works,
    service_credentials,
):
    token_info = await obtain_or_refresh_token(
        service_user_credentials=service_credentials,
        existing_token_info=token_info_access_valid_refresh_overdue,
    )

    # original token should be returned, since it is still valid enough:
    assert token_info == token_info_access_valid_refresh_overdue

    # no token obtain or refresh:
    assert obtain_token_works.num_called == 0
    assert refresh_token_works.num_called == 0


@pytest.mark.asyncio
async def test_obtain_refresh_logic_new_token_obtain_fails(
    obtain_token_raises,
    refresh_token_works,
    service_credentials,
):
    with pytest.raises(ServiceAuthenticationError) as _exc:
        _token_info = await obtain_or_refresh_token(
            service_user_credentials=service_credentials,
            existing_token_info=None,
        )

    assert obtain_token_raises.num_called == 1
    assert refresh_token_works.num_called == 0


@pytest.mark.asyncio
async def test_obtain_refresh_logic_refresh_raises_obtain_works(
    token_info_access_overdue_refresh_valid,
    obtain_token_works,
    refresh_token_raises,
    service_credentials,
    result_token_info,
):
    token_info = await obtain_or_refresh_token(
        service_user_credentials=service_credentials,
        existing_token_info=token_info_access_overdue_refresh_valid,
    )

    # mock generates None:
    assert token_info == result_token_info

    # both are called: refresh token is called and raises, then
    # obtain token is called instead:
    assert obtain_token_works.num_called == 1
    assert refresh_token_raises.num_called == 1

    assert len(obtain_token_works.last_called_args) == 1
    assert obtain_token_works.last_called_args[0] == service_credentials


def test_get_access_token_manager(service_credentials, obtain_token_works, result_token_info):
    test_uuid_key = "test_" + str(uuid4())
    token_mgr = create_or_get_named_access_token_manager(test_uuid_key, service_credentials)

    access_token_str = token_mgr.sync_get_access_token()

    assert access_token_str == "result_access_token"  # noqa: S105

    # load cached works
    token_mgr = create_or_get_named_access_token_manager(test_uuid_key, service_credentials)
