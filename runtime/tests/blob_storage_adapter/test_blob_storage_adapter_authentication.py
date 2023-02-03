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
    obtain_credential_info_from_rest_api,
    obtain_or_refresh_credential_info,
    parse_credential_info_from_xml_string,
)
from hetdesrun.adapters.blob_storage.exceptions import StorageAuthenticationError
from hetdesrun.webservice.auth_outgoing import (
    ClientCredentialsGrantCredentials,
    ServiceCredentials,
)
from hetdesrun.webservice.config import ExternalAuthMode


def test_blob_storage_authentication_parse_credential_info_from_xml_string():
    now = datetime.fromisoformat("2023-01-31T11:08:05+00:00")
    xml_response_text = """
    <AssumeRoleWithWebIdentityResponse xmlns="https://sts.amazonaws.com/doc/2011-06-15/">
        <AssumeRoleWithWebIdentityResult>
            <AssumedRoleUser>
                <Arn></Arn>
                <AssumeRoleId></AssumeRoleId>
            </AssumedRoleUser>
            <Credentials>
                <AccessKeyId>82Q5PD5XG8LNUR9IEOJ0</AccessKeyId>
                <SecretAccessKey>HlZQdbbJNAzhttjDg3pgjU8Nn8BYY0oShqFgMb7M</SecretAccessKey>
                <SessionToken>eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3NLZXkiOiI4MlE1UEQ1WEc4TE5VUjlJRU9KMCIsImFsbG93ZWQtb3JpZ2lucyI6WyJodHRwczovL2Rlc2lnbmVyLWVnbHYtenJwLmRldi5kc2EtaWQuZGUiLCJodHRwOi8vbG9jYWxob3N0Il0sImF1ZCI6ImFjY291bnQiLCJhdXRoX3RpbWUiOjE2NzUxNjU2ODEsImF6cCI6InpycC1oZXRpZGFkZXNpZ25lciIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwiZXhwIjoxNjc1MTY2ODgyLCJncm91cHMiOlsiMjEiXSwiaWF0IjoxNjc1MTY1NjgyLCJpc3MiOiJodHRwczovL3pycC1pZHAuZGV2LmRzYS1pZC5kZS9hdXRoL3JlYWxtcy9lZ2x2LXpycCIsImp0aSI6Ijc4NjAwM2U0LTk5ZTYtNDg2ZS04YjRmLTI1ODIxYjM2OWViOCIsIm5vbmNlIjoiY2Y2MzJhZDA5NmViOGU4MmIxOTc1MDYxZjJkYzgxYmU2ZFBjVVVidGoiLCJwb2xpY3kiOiJyZWFkd3JpdGUiLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJkZXNpZ25lcjEiLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsiRGVzaWduZXIiLCJvZmZsaW5lX2FjY2VzcyIsInVtYV9hdXRob3JpemF0aW9uIiwiSW5mbyIsIkVkaXRvciJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sInJvbGVzIjpbIkRlc2lnbmVyIiwib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiIsIkluZm8iLCJFZGl0b3IiXSwic2NvcGUiOiJvcGVuaWQgZW1haWwgcHJvZmlsZSBvZmZsaW5lX2FjY2VzcyIsInNlc3Npb25fc3RhdGUiOiIzMWI4OTFmNC02YmRmLTRmOGYtOTA5Yi00NWRhNzQ0MjM2MzciLCJzaWQiOiIzMWI4OTFmNC02YmRmLTRmOGYtOTA5Yi00NWRhNzQ0MjM2MzciLCJzdWIiOiIzN2I0OWMxMi1hZThhLTQyNWUtYmJhYS00ZjBmODM5MjIyZGYiLCJ0eXAiOiJCZWFyZXIifQ.ca0m1-Wsa9u31J9LLKUazouu-WI02E58NW4iJ0PQ6fiEU67YmaIbmdfpPkVpt-KB2es_vSvxnUTOqInzAJN0Lw</SessionToken>
                <Expiration>2023-01-31T12:08:02Z</Expiration>
            </Credentials>
            <SubjectFromWebIdentityToken>37b49c12-ae8a-425e-bbaa-4f0f839222df</SubjectFromWebIdentityToken>
        </AssumeRoleWithWebIdentityResult>
        <ResponseMetadata><RequestId>173F62A5F8F1DC8B</RequestId></ResponseMetadata>
    </AssumeRoleWithWebIdentityResponse>
    """
    credential_info = parse_credential_info_from_xml_string(xml_response_text, now)
    assert credential_info.credentials.access_key_id == "82Q5PD5XG8LNUR9IEOJ0"
    assert (
        credential_info.credentials.secret_access_key
        == "HlZQdbbJNAzhttjDg3pgjU8Nn8BYY0oShqFgMb7M"
    )
    assert (
        credential_info.credentials.session_token
        == "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3NLZXkiOiI4MlE1UEQ1WEc4TE5VUjlJRU9KMCIsImFsbG93ZWQtb3JpZ2lucyI6WyJodHRwczovL2Rlc2lnbmVyLWVnbHYtenJwLmRldi5kc2EtaWQuZGUiLCJodHRwOi8vbG9jYWxob3N0Il0sImF1ZCI6ImFjY291bnQiLCJhdXRoX3RpbWUiOjE2NzUxNjU2ODEsImF6cCI6InpycC1oZXRpZGFkZXNpZ25lciIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwiZXhwIjoxNjc1MTY2ODgyLCJncm91cHMiOlsiMjEiXSwiaWF0IjoxNjc1MTY1NjgyLCJpc3MiOiJodHRwczovL3pycC1pZHAuZGV2LmRzYS1pZC5kZS9hdXRoL3JlYWxtcy9lZ2x2LXpycCIsImp0aSI6Ijc4NjAwM2U0LTk5ZTYtNDg2ZS04YjRmLTI1ODIxYjM2OWViOCIsIm5vbmNlIjoiY2Y2MzJhZDA5NmViOGU4MmIxOTc1MDYxZjJkYzgxYmU2ZFBjVVVidGoiLCJwb2xpY3kiOiJyZWFkd3JpdGUiLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJkZXNpZ25lcjEiLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsiRGVzaWduZXIiLCJvZmZsaW5lX2FjY2VzcyIsInVtYV9hdXRob3JpemF0aW9uIiwiSW5mbyIsIkVkaXRvciJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sInJvbGVzIjpbIkRlc2lnbmVyIiwib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiIsIkluZm8iLCJFZGl0b3IiXSwic2NvcGUiOiJvcGVuaWQgZW1haWwgcHJvZmlsZSBvZmZsaW5lX2FjY2VzcyIsInNlc3Npb25fc3RhdGUiOiIzMWI4OTFmNC02YmRmLTRmOGYtOTA5Yi00NWRhNzQ0MjM2MzciLCJzaWQiOiIzMWI4OTFmNC02YmRmLTRmOGYtOTA5Yi00NWRhNzQ0MjM2MzciLCJzdWIiOiIzN2I0OWMxMi1hZThhLTQyNWUtYmJhYS00ZjBmODM5MjIyZGYiLCJ0eXAiOiJCZWFyZXIifQ.ca0m1-Wsa9u31J9LLKUazouu-WI02E58NW4iJ0PQ6fiEU67YmaIbmdfpPkVpt-KB2es_vSvxnUTOqInzAJN0Lw"
    )
    assert credential_info.issue_timestamp.isoformat() == "2023-01-31T11:08:05+00:00"
    assert credential_info.expiration_time_in_seconds == 3597

    parse_error_response_text = "asdfasdf"
    with pytest.raises(StorageAuthenticationError) as exc_info:
        parse_credential_info_from_xml_string(parse_error_response_text, now)
    assert "Cannot parse authentication request response as XML" in str(exc_info.value)

    unexpected_xml_response_text = "<Code>AccessDenied</Code>"
    with pytest.raises(StorageAuthenticationError) as exc_info:
        parse_credential_info_from_xml_string(unexpected_xml_response_text, now)
    assert "The authentication request does not have the expected structure" in str(
        exc_info.value
    )

    error_xml_response_text = """
    <Error>
        <Code>AccessDenied</Code>
        <Message>Access Denied.</Message>
        <Resource>/</Resource>
        <RequestId>173F1539BE0F18F9</RequestId>
        <HostId>9597299a-6a20-4aed-8f65-39688096cd70</HostId>
    </Error>
    """
    with pytest.raises(StorageAuthenticationError) as exc_info:
        parse_credential_info_from_xml_string(error_xml_response_text, now)
    assert "Code: AccessDenied" in str(exc_info.value)
    assert "Message: Access Denied." in str(exc_info.value)

    missing_session_token_xml_response_text = """
    <AssumeRoleWithWebIdentityResponse xmlns="https://sts.amazonaws.com/doc/2011-06-15/">
        <AssumeRoleWithWebIdentityResult>
            <AssumedRoleUser>
                <Arn></Arn>
                <AssumeRoleId></AssumeRoleId>
            </AssumedRoleUser>
            <Credentials>
                <AccessKeyId>82Q5PD5XG8LNUR9IEOJ0</AccessKeyId>
                <SecretAccessKey>HlZQdbbJNAzhttjDg3pgjU8Nn8BYY0oShqFgMb7M</SecretAccessKey>
                <Expiration>2023-01-31T12:08:02Z</Expiration>
            </Credentials>
            <SubjectFromWebIdentityToken>37b49c12-ae8a-425e-bbaa-4f0f839222df</SubjectFromWebIdentityToken>
        </AssumeRoleWithWebIdentityResult>
        <ResponseMetadata><RequestId>173F62A5F8F1DC8B</RequestId></ResponseMetadata>
    </AssumeRoleWithWebIdentityResponse>
    """
    with pytest.raises(StorageAuthenticationError) as exc_info:
        parse_credential_info_from_xml_string(
            missing_session_token_xml_response_text, now
        )
    assert "Could not find at least one of the required Credentials" in str(
        exc_info.value
    )


@pytest.fixture(scope="function")
def credentials() -> Credentials:
    return Credentials(
        access_key_id="some_id",
        secret_access_key="some_key",
        session_token="some_token",
    )


def test_blob_storage_authentication_obtain_credential_info_from_rest_api(credentials):
    with mock.patch(
        "hetdesrun.adapters.blob_storage.authentication.requests.post",
        return_value=mock.Mock(status_code=201, text="text"),
    ):
        with mock.patch(
            "hetdesrun.adapters.blob_storage.authentication.parse_credential_info_from_xml_string",
            return_value=CredentialInfo(
                credentials=credentials,
                issue_timestamp=datetime.fromisoformat("2023-01-31T11:08:05+00:00"),
                expiration_time_in_seconds=3600,
            ),
        ):
            credential_info = obtain_credential_info_from_rest_api("access_token")
            assert credential_info.credentials == credentials
            assert (
                credential_info.issue_timestamp.isoformat()
                == "2023-01-31T11:08:05+00:00"
            )
            assert credential_info.expiration_time_in_seconds == 3600

        with mock.patch(
            "hetdesrun.adapters.blob_storage.authentication.parse_credential_info_from_xml_string",
            side_effect=StorageAuthenticationError("error message"),
        ):
            with pytest.raises(StorageAuthenticationError) as exc_info:
                obtain_credential_info_from_rest_api("access_token")

            assert "error message" == str(exc_info.value)

    with mock.patch(
        "hetdesrun.adapters.blob_storage.authentication.requests.post",
        return_value=mock.Mock(status_code=333, text="error"),
    ):
        with pytest.raises(StorageAuthenticationError) as exc_info:
            obtain_credential_info_from_rest_api("access_token")

        assert "BLOB storage credential request returned with status code 333" in str(
            exc_info.value
        )
        assert "and response text:\nerror\n" in str(exc_info.value)


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
        with pytest.raises(StorageAuthenticationError) as exc_info:
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
        with pytest.raises(StorageAuthenticationError) as exc_info:
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
