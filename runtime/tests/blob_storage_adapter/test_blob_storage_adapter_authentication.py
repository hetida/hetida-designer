from datetime import datetime, timedelta, timezone
from unittest import mock

import pytest

from hetdesrun.adapters.blob_storage.authentication import (
    CredentialInfo,
    Credentials,
    StorageAuthenticationError,
    create_or_get_named_credential_manager,
    credentials_still_valid_enough,
    get_access_token,
    get_credentials,
    obtain_or_refresh_credential_info,
)
from hetdesrun.adapters.blob_storage.exceptions import NoAccessTokenAvailable
from hetdesrun.webservice.auth_outgoing import (
    ClientCredentialsGrantCredentials,
    ServiceCredentials,
)
from hetdesrun.webservice.config import ExternalAuthMode


def test_blob_storage_authentication_obtain_credential_info_from_rest_api():
    pass


@pytest.fixture(scope="function")
def credentials() -> Credentials:
    return Credentials(
        access_key_id="some_id",
        secret_access_key="some_key",
        session_token="some_token",
    )


def test_blob_storage_authentication_credentials_still_valid_enough(credentials):
    credential_info = CredentialInfo(
        credentials=credentials,
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
def credential_info_longer_valid(credentials) -> CredentialInfo:
    return CredentialInfo(
        credentials=credentials,
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


def test_blob_storage_authentication_obtain_or_refresh_credential_info_still_valid(
    credential_info_longer_valid,
    result_credential_info,
    access_token,
):
    with mock.patch(
        "hetdesrun.adapters.blob_storage.authentication.obtain_credential_info_from_rest_api",
        return_value=result_credential_info,
    ) as mocked_obtain_credential_info_from_rest_api:
        credential_info = obtain_or_refresh_credential_info(
            access_token=access_token,
            existing_credential_info=credential_info_longer_valid,
        )

        # original credential info should be returned, since it is still valid.
        assert credential_info == credential_info_longer_valid

        # not token obtain:
        assert mocked_obtain_credential_info_from_rest_api.call_count == 0


def test_blob_storage_authentication_obtain_or_refresh_credential_info_new_works(
    access_token,
    result_credential_info,
):
    with mock.patch(
        "hetdesrun.adapters.blob_storage.authentication.obtain_credential_info_from_rest_api",
        return_value=result_credential_info,
    ) as mocked_obtain_credential_info_from_rest_api:
        credential_info = obtain_or_refresh_credential_info(
            access_token=access_token, existing_credential_info=None
        )

        # original credential info should be returned, since it is still valid.
        assert credential_info == result_credential_info

        # not token obtain:
        assert mocked_obtain_credential_info_from_rest_api.call_count == 1


def test_blob_storage_authentication_obtain_or_refresh_credential_info_refresh_works(
    credential_info_overdue,
    access_token,
    result_credential_info,
):
    with mock.patch(
        "hetdesrun.adapters.blob_storage.authentication.obtain_credential_info_from_rest_api",
        return_value=result_credential_info,
    ) as mocked_obtain_credential_info_from_rest_api:
        credential_info = obtain_or_refresh_credential_info(
            access_token=access_token, existing_credential_info=credential_info_overdue
        )

        # original credential info should be returned, since it is still valid.
        assert credential_info == result_credential_info

        # not token obtain:
        assert mocked_obtain_credential_info_from_rest_api.call_count == 1


def test_blob_storage_authentication_obtain_or_refresh_credential_info_new_raises(
    access_token,
):
    with mock.patch(
        "hetdesrun.adapters.blob_storage.authentication.obtain_credential_info_from_rest_api",
        side_effect=StorageAuthenticationError,
    ) as mocked_obtain_credential_info_from_rest_api_raises:
        with pytest.raises(StorageAuthenticationError):
            obtain_or_refresh_credential_info(
                access_token=access_token, existing_credential_info=None
            )

        # not token obtain:
        assert mocked_obtain_credential_info_from_rest_api_raises.call_count == 1


def test_blob_storage_authentication_obtain_or_refresh_credential_info_refresh_raises(
    credential_info_overdue,
    access_token,
):
    with mock.patch(
        "hetdesrun.adapters.blob_storage.authentication.obtain_credential_info_from_rest_api",
        side_effect=StorageAuthenticationError,
    ) as mocked_obtain_credential_info_from_rest_api_raises:
        with pytest.raises(StorageAuthenticationError):
            credential_info = obtain_or_refresh_credential_info(
                access_token=access_token,
                existing_credential_info=credential_info_overdue,
            )

        # not token obtain:
        assert mocked_obtain_credential_info_from_rest_api_raises.call_count == 1


def test_blob_storage_adapter_create_or_get_named_credential_manager(
    result_credential_info, access_token
):
    with mock.patch(
        "hetdesrun.adapters.blob_storage.authentication.obtain_credential_info_from_rest_api",
        return_value=result_credential_info,
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


@pytest.fixture(scope="function")
def service_credentials():
    return ServiceCredentials(
        realm="my-realm",
        grant_credentials=ClientCredentialsGrantCredentials(
            client_id="my-client", client_secret="abcd"
        ),
        auth_url="https://test.com/auth",
        post_client_kwargs={"verify": False},
    )


def test_blob_storage_adapter_get_access_token(access_token):
    with mock.patch(
        "hetdesrun.adapters.blob_storage.authentication.get_config",
        return_value=mock.Mock(external_auth_mode=ExternalAuthMode.OFF),
    ):
        with pytest.raises(NoAccessTokenAvailable) as exc_info:
            get_access_token()
        assert (
            "Config option external_auth_mode is set to 'OFF' "
            "thus no access token is available!"
        ) in str(exc_info.value)

    with mock.patch(
        "hetdesrun.adapters.blob_storage.authentication.get_config",
        return_value=mock.Mock(external_auth_mode=ExternalAuthMode.FORWARD_OR_FIXED),
    ):
        with mock.patch(
            "hetdesrun.adapters.blob_storage.authentication.forward_request_token_or_get_fixed_token_auth_headers",
            return_value={"Authorization": "Bearer " + access_token},
        ):
            assert get_access_token() == access_token

    with mock.patch(
        "hetdesrun.adapters.blob_storage.authentication.get_config",
        return_value=mock.Mock(external_auth_mode=ExternalAuthMode.CLIENT),
    ):
        token_manager_mock = mock.Mock()
        token_manager_mock.sync_get_access_token = mock.MagicMock(
            return_value=access_token
        )
        with mock.patch(
            "hetdesrun.adapters.blob_storage.authentication.create_or_get_named_access_token_manager",
            return_value=token_manager_mock,
        ):
            assert get_access_token() == access_token

    with mock.patch(
        "hetdesrun.adapters.blob_storage.authentication.get_config",
        return_value=mock.Mock(external_auth_mode=""),
    ):
        with pytest.raises(NoAccessTokenAvailable) as exc_info:
            get_access_token()
        assert (
            "Unknown config option for external_auth_mode '' "
            "thus no access token is available!"
        ) in str(exc_info.value)


def test_blob_storage_adapter_get_credentials(credentials, access_token):
    with mock.patch(
        "hetdesrun.adapters.blob_storage.authentication.get_access_token",
        return_value=access_token,
    ):
        credential_manager_mock = mock.Mock()
        credential_manager_mock.get_credentials = mock.MagicMock(
            return_value=credentials
        )
        with mock.patch(
            "hetdesrun.adapters.blob_storage.authentication.create_or_get_named_credential_manager",
            return_value=credential_manager_mock,
        ):
            assert get_credentials() == credentials
