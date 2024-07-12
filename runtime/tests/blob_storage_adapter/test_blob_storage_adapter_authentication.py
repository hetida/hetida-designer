from datetime import datetime, timedelta, timezone
from unittest import mock

import pytest

from hetdesrun.adapters.blob_storage.authentication import (
    CredentialInfo,
    Credentials,
    create_or_get_named_credential_manager,
    credentials_still_valid_enough,
    extract_namespace_from_root_tag,
    get_access_token,
    get_credentials,
    obtain_credential_info_from_sts_rest_api,
    obtain_or_refresh_credential_info,
    parse_credential_info_from_xml_string,
    parse_xml_error_response,
)
from hetdesrun.adapters.blob_storage.exceptions import StorageAuthenticationError
from hetdesrun.webservice.auth_outgoing import (
    ClientCredentialsGrantCredentials,
    ServiceCredentials,
)


def test_blob_storage_extract_namespace_from_root_tag() -> None:
    root_tag = "{https://sts.amazonaws.com/doc/2011-06-15/}AssumeRoleWithWebIdentityResponse"
    namespace = extract_namespace_from_root_tag(root_tag)
    assert namespace == "https://sts.amazonaws.com/doc/2011-06-15/"


def test_blob_storage_authentication_parse_credential_info_from_xml_string() -> None:
    now = datetime.fromisoformat("2023-01-31T11:08:05+00:00")
    xml_response_text = """
    <AssumeRoleWithWebIdentityResponse xmlns="https://sts.amazonaws.com/doc/2011-06-15/">
        <AssumeRoleWithWebIdentityResult>
            <AssumedRoleUser>
                <Arn></Arn>
                <AssumeRoleId></AssumeRoleId>
            </AssumedRoleUser>
            <Credentials>
                <AccessKeyId>access_key_id</AccessKeyId>
                <SecretAccessKey>secret_access_key</SecretAccessKey>
                <SessionToken>session_token</SessionToken>
                <Expiration>2023-01-31T12:08:02Z</Expiration>
            </Credentials>
            <SubjectFromWebIdentityToken>subject_from_web_identity_token</SubjectFromWebIdentityToken>
        </AssumeRoleWithWebIdentityResult>
        <ResponseMetadata><RequestId>request_id</RequestId></ResponseMetadata>
    </AssumeRoleWithWebIdentityResponse>
    """
    credential_info = parse_credential_info_from_xml_string(xml_response_text, now)
    assert credential_info.credentials.access_key_id == "access_key_id"
    assert (
        credential_info.credentials.secret_access_key == "secret_access_key"  # noqa: S105
    )
    assert credential_info.credentials.session_token == "session_token"  # noqa: S105
    assert credential_info.issue_timestamp.isoformat() == "2023-01-31T11:08:05+00:00"
    assert credential_info.expiration_time_in_seconds == 3597

    parse_error_response_text = "asdfasdf"
    with pytest.raises(StorageAuthenticationError) as exc_info:
        parse_credential_info_from_xml_string(parse_error_response_text, now)
    assert "Cannot parse authentication request response as XML" in str(exc_info.value)

    unexpected_xml_response_text = "<Code>AccessDenied</Code>"
    with pytest.raises(StorageAuthenticationError) as exc_info:
        parse_credential_info_from_xml_string(unexpected_xml_response_text, now)
    assert "The authentication request does not have the expected structure" in str(exc_info.value)

    missing_session_token_xml_response_text = """
    <AssumeRoleWithWebIdentityResponse xmlns="https://sts.amazonaws.com/doc/2011-06-15/">
        <AssumeRoleWithWebIdentityResult>
            <AssumedRoleUser>
                <Arn></Arn>
                <AssumeRoleId></AssumeRoleId>
            </AssumedRoleUser>
            <Credentials>
                <AccessKeyId>access_key_id</AccessKeyId>
                <SecretAccessKey>secret_access_key</SecretAccessKey>
                <Expiration>2023-01-31T12:08:02Z</Expiration>
            </Credentials>
            <SubjectFromWebIdentityToken>subject_from_web_identity_token</SubjectFromWebIdentityToken>
        </AssumeRoleWithWebIdentityResult>
        <ResponseMetadata><RequestId>request_id</RequestId></ResponseMetadata>
    </AssumeRoleWithWebIdentityResponse>
    """  # noqa: S105
    with pytest.raises(StorageAuthenticationError) as exc_info:
        parse_credential_info_from_xml_string(missing_session_token_xml_response_text, now)
    assert "At least one of the required Credentials could not be found" in str(exc_info.value)


def test_blob_storage_authentication_parse_xml_error_response() -> None:
    error_xml_response_text = """
    <ErrorResponse xmlns="https://sts.amazonaws.com/doc/2011-06-15/">
        <Error>
            <Type></Type>
            <Code>InvalidParameterValue</Code>
            <Message>Error processing RoleArn parameter: RoleARN parse err: Invalid ARN</Message>
        </Error>
        <RequestId>17467834FFE4296F</RequestId>
    </ErrorResponse>
    """
    error = parse_xml_error_response(error_xml_response_text)
    assert "InvalidParameterValue" in error
    assert "Error processing RoleArn parameter: RoleARN parse err: Invalid ARN" in error


@pytest.fixture()
def credentials() -> Credentials:
    return Credentials(
        access_key_id="some_id",
        secret_access_key="some_key",  # noqa: S106
        session_token="some_token",  # noqa: S106
    )


@pytest.mark.asyncio
async def test_blob_storage_authentication_obtain_credential_info_from_sts_rest_api(
    access_token: str,
    credentials: Credentials,
) -> None:
    with mock.patch(
        "hetdesrun.adapters.blob_storage.authentication.get_access_token",
        return_value=mock.AsyncMock(return_value=access_token),
    ):
        with mock.patch(
            "hetdesrun.adapters.blob_storage.authentication.httpx.AsyncClient.post",
            return_value=mock.Mock(status_code=200, text="text"),
        ):
            with mock.patch(
                "hetdesrun.adapters.blob_storage.authentication.parse_credential_info_from_xml_string",
                return_value=CredentialInfo(
                    credentials=credentials,
                    issue_timestamp=datetime.fromisoformat("2023-01-31T11:08:05+00:00"),
                    expiration_time_in_seconds=3600,
                ),
            ):
                credential_info = await obtain_credential_info_from_sts_rest_api()
                assert credential_info.credentials == credentials
                assert credential_info.issue_timestamp.isoformat() == "2023-01-31T11:08:05+00:00"
                assert credential_info.expiration_time_in_seconds == 3600

            with (
                mock.patch(
                    "hetdesrun.adapters.blob_storage.authentication.parse_credential_info_from_xml_string",
                    side_effect=StorageAuthenticationError,
                ),
                pytest.raises(StorageAuthenticationError),
            ):
                await obtain_credential_info_from_sts_rest_api()

        with mock.patch(
            "hetdesrun.adapters.blob_storage.authentication.httpx.AsyncClient.post",
            return_value=mock.Mock(
                status_code=400,
                text="""
                <ErrorResponse xmlns="https://sts.amazonaws.com/doc/2011-06-15/">
                    <Error>
                        <Type></Type>
                        <Code>InvalidParameterValue</Code>
                        <Message>Error processing RoleArn parameter: RoleARN parse err</Message>
                    </Error>
                    <RequestId>17467834FFE4296F</RequestId>
                </ErrorResponse>
                """,
            ),
        ):
            with pytest.raises(StorageAuthenticationError) as exc_info:
                await obtain_credential_info_from_sts_rest_api()

            assert "Error Code:" in str(exc_info.value)
            assert "InvalidParameterValue" in str(exc_info.value)
            assert "Error processing RoleArn parameter" in str(exc_info.value)


def test_blob_storage_authentication_credentials_still_valid_enough(
    credentials: Credentials,
) -> None:
    credential_info = CredentialInfo(
        credentials=credentials,
        issue_timestamp=(datetime.now(timezone.utc) - timedelta(minutes=5)),
        expiration_time_in_seconds=3600,
    )

    assert credentials_still_valid_enough(credential_info) is True

    credential_info.issue_timestamp = credential_info.issue_timestamp - timedelta(minutes=50)

    assert credentials_still_valid_enough(credential_info) is False


@pytest.fixture()
def access_token() -> str:
    return "1234"


@pytest.fixture()
def result_credential_info() -> CredentialInfo:
    return CredentialInfo(
        credentials=Credentials(
            access_key_id="result_id",
            secret_access_key="result_key",  # noqa: S106
            session_token="result_token",  # noqa: S106
        ),
        expiration_time_in_seconds=3600,
        issue_timestamp=datetime.now(timezone.utc),
    )


@pytest.fixture()
def credential_info_longer_valid(credentials: Credentials) -> CredentialInfo:
    return CredentialInfo(
        credentials=credentials,
        expiration_time_in_seconds=3600,
        issue_timestamp=datetime.now(timezone.utc),
    )


@pytest.fixture()
def credential_info_overdue() -> CredentialInfo:
    return CredentialInfo(
        credentials=Credentials(
            access_key_id="some_id",
            secret_access_key="some_key",  # noqa: S106
            session_token="some_token",  # noqa: S106
        ),
        expiration_time_in_seconds=-1,
        issue_timestamp=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_blob_storage_authentication_obtain_or_refresh_credential_info_still_valid(
    credential_info_longer_valid: CredentialInfo,
    result_credential_info: CredentialInfo,
) -> None:
    with mock.patch(
        "hetdesrun.adapters.blob_storage.authentication.obtain_credential_info_from_sts_rest_api",
        return_value=result_credential_info,
    ) as mocked_obtain_credential_info_from_sts_rest_api:
        credential_info = await obtain_or_refresh_credential_info(
            existing_credential_info=credential_info_longer_valid,
        )

        # original credential info should be returned, since it is still valid.
        assert credential_info == credential_info_longer_valid

        # not token obtain:
        assert mocked_obtain_credential_info_from_sts_rest_api.call_count == 0


@pytest.mark.asyncio
async def test_blob_storage_authentication_obtain_or_refresh_credential_info_new_works(
    result_credential_info: CredentialInfo,
) -> None:
    with mock.patch(
        "hetdesrun.adapters.blob_storage.authentication.obtain_credential_info_from_sts_rest_api",
        return_value=result_credential_info,
    ) as mocked_obtain_credential_info_from_sts_rest_api:
        credential_info = await obtain_or_refresh_credential_info(existing_credential_info=None)

        # original credential info should be returned, since it is still valid.
        assert credential_info == result_credential_info

        # not token obtain:
        assert mocked_obtain_credential_info_from_sts_rest_api.call_count == 1


@pytest.mark.asyncio
async def test_blob_storage_authentication_obtain_or_refresh_credential_info_refresh_works(
    credential_info_overdue: CredentialInfo,
    result_credential_info: CredentialInfo,
) -> None:
    with mock.patch(
        "hetdesrun.adapters.blob_storage.authentication.obtain_credential_info_from_sts_rest_api",
        return_value=result_credential_info,
    ) as mocked_obtain_credential_info_from_sts_rest_api:
        credential_info = await obtain_or_refresh_credential_info(
            existing_credential_info=credential_info_overdue
        )

        # original credential info should be returned, since it is still valid.
        assert credential_info == result_credential_info

        # not token obtain:
        assert mocked_obtain_credential_info_from_sts_rest_api.call_count == 1


@pytest.mark.asyncio
async def test_blob_storage_authentication_obtain_or_refresh_credential_info_new_raises() -> None:
    with mock.patch(
        "hetdesrun.adapters.blob_storage.authentication.obtain_credential_info_from_sts_rest_api",
        side_effect=StorageAuthenticationError,
    ) as mocked_obtain_credential_info_from_sts_rest_api_raises:
        with pytest.raises(StorageAuthenticationError):
            await obtain_or_refresh_credential_info(existing_credential_info=None)

        # not token obtain:
        assert mocked_obtain_credential_info_from_sts_rest_api_raises.call_count == 1


@pytest.mark.asyncio
async def test_blob_storage_authentication_obtain_or_refresh_credential_info_refresh_raises(
    credential_info_overdue: CredentialInfo,
) -> None:
    with mock.patch(
        "hetdesrun.adapters.blob_storage.authentication.obtain_credential_info_from_sts_rest_api",
        side_effect=StorageAuthenticationError,
    ) as mocked_obtain_credential_info_from_sts_rest_api_raises:
        with pytest.raises(StorageAuthenticationError):
            await obtain_or_refresh_credential_info(
                existing_credential_info=credential_info_overdue,
            )

        # not token obtain:
        assert mocked_obtain_credential_info_from_sts_rest_api_raises.call_count == 1


@pytest.mark.asyncio
async def test_blob_storage_adapter_create_or_get_named_credential_manager(
    result_credential_info: CredentialInfo,
) -> None:
    with mock.patch(
        "hetdesrun.adapters.blob_storage.authentication.obtain_credential_info_from_sts_rest_api",
        return_value=result_credential_info,
    ):
        credential_manager = create_or_get_named_credential_manager(key="key")
        credentials = await credential_manager.get_credentials()

        assert credentials.access_key_id == "result_id"
        assert credentials.secret_access_key == "result_key"  # noqa: S105
        assert credentials.session_token == "result_token"  # noqa: S105

        # load cached works
        credential_manager = create_or_get_named_credential_manager(key="key")


@pytest.fixture()
def service_credentials() -> ServiceCredentials:
    return ServiceCredentials(
        realm="my-realm",
        grant_credentials=ClientCredentialsGrantCredentials(
            client_id="my-client",
            client_secret="abcd",  # noqa: S106
        ),
        auth_url="https://test.com/auth",
        post_client_kwargs={"verify": False},
    )


@pytest.mark.asyncio
async def test_blob_storage_adapter_get_access_token(access_token: str) -> None:
    with mock.patch(
        "hetdesrun.adapters.blob_storage.authentication.get_auth_headers",
        return_value={"Authorization": "Bearer " + access_token},
    ):
        assert await get_access_token() == access_token

    with (
        mock.patch(
            "hetdesrun.adapters.blob_storage.authentication.get_auth_headers",
            side_effect=ValueError,
        ),
        pytest.raises(StorageAuthenticationError, match="Cannot get access token"),
    ):
        await get_access_token()

    with (
        mock.patch(
            "hetdesrun.adapters.blob_storage.authentication.get_auth_headers",
            return_value={},
        ),
        pytest.raises(StorageAuthenticationError, match="Cannot extract access token"),
    ):
        await get_access_token()

    with mock.patch(
        "hetdesrun.adapters.blob_storage.authentication.get_auth_headers",
        return_value={"Authorization": access_token},
    ):
        assert await get_access_token() == access_token


@pytest.mark.asyncio
async def test_blob_storage_adapter_get_credentials(credentials: Credentials) -> None:
    credential_manager_mock = mock.Mock()
    credential_manager_mock.get_credentials = mock.AsyncMock(return_value=credentials)
    with mock.patch(
        "hetdesrun.adapters.blob_storage.authentication.create_or_get_named_credential_manager",
        return_value=credential_manager_mock,
    ):
        returned_credentials = await get_credentials()
        assert returned_credentials == credentials
