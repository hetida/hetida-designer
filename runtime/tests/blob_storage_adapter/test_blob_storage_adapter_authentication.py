from copy import deepcopy
from datetime import datetime, timedelta, timezone
from unittest import mock

import pytest

from hetdesrun.webservice.auth_outgoing import ClientCredentialsGrantCredentials, ServiceCredentials
from hetdesrun.adapters.blob_storage.authentication import (
    CredentialInfo,
    Credentials,
    StsAuthenticationError,
    create_or_get_named_credential_manager,
    credentials_still_valid_enough,
    get_access_token,
    get_credentials,
    obtain_credential_info_from_sts,
    obtain_or_refresh_credential_info,
)


def test_blob_storage_authentication_obtain_credential_info_from_sts():
    pass


def test_blob_storage_authentication_credentials_still_valid_enough():
    credential_info = CredentialInfo(
        credentials=Credentials(
            access_key_id="world", secret_access_key="hello", session_token="1234"
        ),
        issue_timestamp=(datetime.now(timezone.utc) - timedelta(minutes=5)),
        expiration_time_in_seconds=3600,
    )

    assert credentials_still_valid_enough(credential_info) is True

    credential_info.issue_timestamp = credential_info.issue_timestamp - timedelta(
        minutes=50
    )

    assert credentials_still_valid_enough(credential_info) is False


@pytest.fixture(scope="function")
def access_token():
    return "1234"


@pytest.fixture(scope="function")
def result_credential_info() -> CredentialInfo:
    return CredentialInfo(
        credentials=Credentials(
            access_key_id="result_id",
            secret_access_key="result_key",
            session_token="result_token",
        ),
        expiration_time_in_seconds=3600,
        issue_timestamp=datetime.now(timezone.utc),
    )


@pytest.fixture(scope="function")
def credential_info_longer_valid() -> CredentialInfo:
    return CredentialInfo(
        credentials=Credentials(
            access_key_id="some_id",
            secret_access_key="some_key",
            session_token="some_token",
        ),
        expiration_time_in_seconds=3600,
        issue_timestamp=datetime.now(timezone.utc),
    )


@pytest.fixture(scope="function")
def credential_info_overdue() -> CredentialInfo:
    return CredentialInfo(
        credentials=Credentials(
            access_key_id="some_id",
            secret_access_key="some_key",
            session_token="some_token",
        ),
        expiration_time_in_seconds=-1,
        issue_timestamp=datetime.now(timezone.utc),
    )


@pytest.fixture(scope="function")
def mock_obtain_or_refresh_credential_info_works(result_credential_info):
    def mocked_obtain_func(*args, **kwargs):
        mocked_obtain_func.last_called_args = deepcopy(args)
        mocked_obtain_func.last_called_kwargs = deepcopy(kwargs)
        mocked_obtain_func.num_called += 1
        return result_credential_info

    mocked_obtain_func.num_called = 0

    with mock.patch(
        "hetdesrun.adapters.blob_storage.authentication.obtain_credential_info_from_sts",
        mocked_obtain_func,
    ) as mocked_obtain_or_refresh_credential_info_works:
        return mocked_obtain_or_refresh_credential_info_works


@pytest.fixture(scope="function")
def mock_obtain_or_refresh_credential_info_raises():
    def mocked_obtain_func(*args, **kwargs):
        mocked_obtain_func.last_called_args = deepcopy(args)
        mocked_obtain_func.last_called_kwargs = deepcopy(kwargs)
        mocked_obtain_func.num_called += 1
        raise StsAuthenticationError

    mocked_obtain_func.num_called = 0

    with mock.patch(
        "hetdesrun.adapters.blob_storage.authentication.obtain_credential_info_from_sts",
        mocked_obtain_func,
    ) as _mocked_obtain_or_refresh_credential_info_raises:
        return _mocked_obtain_or_refresh_credential_info_raises


def test_blob_storage_authentication_obtain_or_refresh_credential_info_still_valid(
    credential_info_longer_valid, mock_obtain_or_refresh_credential_info_works, access_token
):
    credential_info = obtain_or_refresh_credential_info(
        access_token=access_token, existing_credential_info=credential_info_longer_valid
    )

    # original credential info should be returned, since it is still valid.
    assert credential_info == credential_info_longer_valid

    # not token obtain:
    assert mock_obtain_or_refresh_credential_info_works.num_called == 0


def test_blob_storage_authentication_obtain_or_refresh_credential_info_new_works(
    mock_obtain_or_refresh_credential_info_works,
    access_token,
    result_credential_info,
):
    credential_info = obtain_or_refresh_credential_info(
        access_token=access_token, existing_credential_info=None
    )

    # original credential info should be returned, since it is still valid.
    assert credential_info == result_credential_info

    # not token obtain:
    assert mock_obtain_or_refresh_credential_info_works.num_called == 1


def test_blob_storage_authentication_obtain_or_refresh_credential_info_refresh_works(
    credential_info_overdue,
    mock_obtain_or_refresh_credential_info_works,
    access_token,
    result_credential_info,
):
    credential_info = obtain_or_refresh_credential_info(
        access_token=access_token, existing_credential_info=credential_info_overdue
    )

    # original credential info should be returned, since it is still valid.
    assert credential_info == result_credential_info

    # not token obtain:
    assert mock_obtain_or_refresh_credential_info_works.num_called == 1


def test_blob_storage_authentication_obtain_or_refresh_credential_info_new_raises(
    mock_obtain_or_refresh_credential_info_raises,
    access_token,
):
    with pytest.raises(StsAuthenticationError):
        credential_info = obtain_or_refresh_credential_info(
            access_token=access_token, existing_credential_info=None
        )

    # not token obtain:
    assert mock_obtain_or_refresh_credential_info_works.num_called == 1


def test_blob_storage_authentication_obtain_or_refresh_credential_info_refresh_raises(
    credential_info_overdue,
    mock_obtain_or_refresh_credential_info_raises,
    access_token,
):
    with pytest.raises(StsAuthenticationError):
        credential_info = obtain_or_refresh_credential_info(
            access_token=access_token, existing_credential_info=credential_info_overdue
        )

    # not token obtain:
    assert mock_obtain_or_refresh_credential_info_works.num_called == 1


def test_blob_storage_adapter_create_or_get_named_credential_manager(
    access_token, mock_obtain_or_refresh_credential_info_works
):
    credential_manager = create_or_get_named_credential_manager(
        key="key", access_token=access_token
    )
    credentials = credential_manager.get_credentials()

    assert credentials.access_key_id == "result_id"
    assert credentials.secret_access_key == "result_key"
    assert credentials.session_token == "result_token"

    # load cached works

    credential_manager = create_or_get_named_credential_manager(
        key="key", access_token=access_token
    )


def test_blob_storage_adapter_get_access_token():
    pass
    # with mock.patch(
    #     "hetdesrun.adapters.blob_storage.authentication.get_config.external_auth_client_credentials",
    #     new_callable=mock.PropertyMock,
    #     return_value=ServiceCredentials(
    #         realm="my-realm",
    #         grant_credentials=ClientCredentialsGrantCredentials(
    #             client_id="my-client", client_secret="abcd"
    #         ),
    #         auth_url="https://test.com/auth",
    #         post_client_kwargs={"verify": False},
    #     )
    # ):
    #     with mock.patch(
    #         "hetdesrun.adapters"
    #     )
        
        


def test_blob_storage_adapter_get_credentials():
    pass
