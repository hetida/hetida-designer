import logging
import threading
import urllib
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from functools import cache

import httpx
from pydantic import BaseModel, Field

from hetdesrun.adapters.blob_storage.config import get_blob_adapter_config
from hetdesrun.adapters.blob_storage.exceptions import StorageAuthenticationError
from hetdesrun.webservice.auth_dependency import get_auth_headers
from hetdesrun.webservice.config import get_config

logger = logging.getLogger(__name__)


class Credentials(BaseModel):
    access_key_id: str
    secret_access_key: str
    session_token: str


class CredentialInfo(BaseModel):
    credentials: Credentials
    issue_timestamp: datetime = Field(
        ...,
        description=(
            "UTC zoned timestamp shortly before requesting token."
            " Is used to calculate expiration time estimates."
        ),
    )
    expiration_time_in_seconds: int


def extract_namespace_from_root_tag(root_tag: str) -> str:
    return root_tag.split("}")[0].strip("{")


def parse_credential_info_from_xml_string(xml_string: str, utc_now: datetime) -> CredentialInfo:
    logger.debug("Parsing XML response to obtain credential info")
    try:
        xml_response = ET.fromstring(xml_string)  # noqa: S314
    except ET.ParseError as error:
        msg = f"Cannot parse authentication request response as XML:\n{error}"
        logger.error(msg)
        raise StorageAuthenticationError(msg) from error
    namespace = {"sts": extract_namespace_from_root_tag(xml_response.tag)}
    if not xml_response.tag.endswith("AssumeRoleWithWebIdentityResponse"):
        msg = f"The authentication request does not have the expected structure:\n{xml_string}"
        logger.error(msg)
        raise StorageAuthenticationError(msg)
    path = "./sts:AssumeRoleWithWebIdentityResult/sts:Credentials/sts:"
    xml_access_key = xml_response.find(path + "AccessKeyId", namespace)
    xml_secret_access_key = xml_response.find(path + "SecretAccessKey", namespace)
    xml_session_token = xml_response.find(path + "SessionToken", namespace)
    xml_expiration = xml_response.find(path + "Expiration", namespace)
    if (
        xml_access_key is None
        or xml_secret_access_key is None
        or xml_session_token is None
        or xml_expiration is None
    ):
        msg = (
            "At least one of the required Credentials could not be found"
            f"in the XML response:\n{xml_string}"
        )
        logger.error(msg)
        raise StorageAuthenticationError(msg)

    credentials = Credentials(
        access_key_id=xml_access_key.text,
        secret_access_key=xml_secret_access_key.text,
        session_token=xml_session_token.text,
    )
    try:
        expiration_time = datetime.fromisoformat(str(xml_expiration.text))
    except ValueError as error:
        msg = (
            f"Expiration '{xml_expiration.text}' from XML response cannot be parsed "
            f"to a datetime:\n{str(error)}"
        )
        raise StorageAuthenticationError(msg) from error
    if expiration_time.tzinfo is None:
        msg = f"Expiration time {xml_expiration.text} must not be timezone naive!"
        raise StorageAuthenticationError(msg)
    expiration_time_in_seconds = (expiration_time - utc_now).total_seconds()

    return CredentialInfo(
        issue_timestamp=utc_now,
        credentials=credentials,
        expiration_time_in_seconds=expiration_time_in_seconds,
    )


def parse_xml_error_response(xml_string: str) -> str:
    try:
        xml_response = ET.fromstring(xml_string)  # noqa: S314
    except ET.ParseError as error:
        msg = f"Cannot parse authentication request response as XML:\n{error}"
        logger.error(msg)
        raise StorageAuthenticationError(msg) from error

    namespace = {"sts": extract_namespace_from_root_tag(xml_response.tag)}
    if xml_response.tag.endswith("ErrorResponse"):
        path = "./sts:Error/sts:"
        error_code = xml_response.find(path + "Code", namespace)
        error_message = xml_response.find(path + "Message", namespace)
        error_code_text = "NOT PROVIDED"
        error_message_text = "NOT PROVIDED"
        try:
            if error_message is not None:
                error_message_text = str(error_message.text)
            if error_code is not None:
                error_code_text = str(error_code.text)
        except AttributeError:
            pass
        return f":\nError Code: {error_code_text}\nError Message: {error_message_text}\n"
    return f"and response text:\n{xml_string}\n"


async def obtain_credential_info_from_sts_rest_api() -> CredentialInfo:
    """Obtain credential info from STS REST API."""
    logger.debug("Obtaining credential info from STS REST API")
    utc_now = datetime.now(timezone.utc)
    access_token = await get_access_token()
    params = {
        "Action": "AssumeRoleWithWebIdentity",
        "WebIdentityToken": access_token,
        **get_blob_adapter_config().sts_params,
    }
    params_string = urllib.parse.urlencode(params, safe=":/")
    async with httpx.AsyncClient(
        verify=get_config().hd_runtime_verify_certs,
        timeout=get_config().external_request_timeout,
        auth=None,
    ) as client:
        response = await client.post(
            url=get_blob_adapter_config().endpoint_url,
            params=params_string,
        )
    if response.status_code != 200:
        msg = f"BLOB storage STS REST API request returned with status code {response.status_code} "
        msg = msg + parse_xml_error_response(response.text)
        msg = msg + (
            f"When calling URL: {get_blob_adapter_config().endpoint_url} "
            f"with query parameters: {params_string}"
        )
        logger.error(msg)
        raise StorageAuthenticationError(msg)

    credential_info = parse_credential_info_from_xml_string(response.text, utc_now)

    return credential_info


def credentials_still_valid_enough(credential_info: CredentialInfo) -> bool:
    now = datetime.now(timezone.utc)

    time_since_issue_in_seconds = (now - credential_info.issue_timestamp).total_seconds()
    logger.debug(
        "%ss since last credentials were issued. Credentials expire after %ss.",
        time_since_issue_in_seconds,
        credential_info.expiration_time_in_seconds,
    )

    return time_since_issue_in_seconds <= credential_info.expiration_time_in_seconds * 0.9


async def obtain_or_refresh_credential_info(
    existing_credential_info: CredentialInfo | None = None,
) -> CredentialInfo:
    """Obtain new credential info if necessary.

    A StorageAuthenticationError raised in obtain_credentail_info_from_rest_api may occur.
    """
    if existing_credential_info is not None:
        if credentials_still_valid_enough(existing_credential_info):
            logger.debug("Existing credentials still valid")
            return existing_credential_info
        logger.debug("Credentials will soon expire. Trying to get new credentials.")

    return await obtain_credential_info_from_sts_rest_api()


class CredentialManager:
    _current_credential_info: CredentialInfo | None

    def __init__(self) -> None:
        self._current_credential_info = None
        self._credential_thread_lock = threading.Lock()

    async def _obtain_or_refresh_credential_info(self) -> None:
        """Obtain new credential info if necessary.

        A StorageAuthenticationError raised in obtain_credentail_info_from_rest_api may occur.
        """
        credential_info = await obtain_or_refresh_credential_info(self._current_credential_info)
        with self._credential_thread_lock:
            self._current_credential_info = credential_info

    async def get_credentials(self) -> Credentials:
        logger.debug("Waiting for credential info")
        await self._obtain_or_refresh_credential_info()
        if self._current_credential_info is None:
            msg = "Obtained credentials are None"
            logger.error(msg)
            raise StorageAuthenticationError(msg)
        return self._current_credential_info.credentials


@cache
def global_credential_manager_dict() -> dict[str, CredentialManager]:
    return {}


def create_or_get_named_credential_manager(key: str) -> CredentialManager:
    manager_dict = global_credential_manager_dict()

    if key in manager_dict:
        logger.debug("Returning existing credential manager for key %s", key)
        return manager_dict[key]

    logger.info("Creating new credential manager for key %s", key)

    manager_dict[key] = CredentialManager()

    return manager_dict[key]


async def get_access_token() -> str:
    try:
        token_header = await get_auth_headers()
    except ValueError as error:
        msg = "Cannot get access token from auth header"
        logger.error(msg)
        raise StorageAuthenticationError(msg) from error
    try:
        access_token = token_header["Authorization"].split("Bearer ")[-1]
    except KeyError as error:
        msg = "Cannot extract access token from auth header"
        logger.error(msg)
        raise StorageAuthenticationError(msg) from error
    return access_token


async def get_credentials() -> Credentials:
    """Get credentials for the BLOB storage.

    A StorageAuthenticationError raised in the CredentialManager method get_credentials may occur.
    """
    credential_manager = create_or_get_named_credential_manager("blob_adapter_cred")
    credentials = await credential_manager.get_credentials()
    logger.debug("Got credentials from credential manager")
    return credentials
