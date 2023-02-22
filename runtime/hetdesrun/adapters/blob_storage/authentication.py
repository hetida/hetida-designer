import logging
import threading
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from functools import cache

import requests
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


def parse_credential_info_from_xml_string(
    xml_string: str, now: datetime
) -> CredentialInfo:
    namespace = {"aws": "https://sts.amazonaws.com/doc/2011-06-15/"}
    try:
        xml_response = ET.fromstring(xml_string)
    except ET.ParseError as error:
        msg = f"Cannot parse authentication request response as XML:\n{error}"
        logger.error(msg)
        raise StorageAuthenticationError(msg) from error
    if not xml_response.tag.endswith("AssumeRoleWithWebIdentityResponse"):
        msg = "The authentication request does not have the expected structure"
        if xml_response.tag == "Error":
            error_code = xml_response.find("Code")
            error_message = xml_response.find("Message")
            error_code_text = "NOT PROVIDED"
            error_message_text = "NOT PROVIDED"
            try:
                if error_message is not None:
                    error_message_text = str(error_message.text)
                if error_code is not None:
                    error_code_text = str(error_code.text)
            except AttributeError:
                pass
            msg = msg + f":\nCode: {error_code_text}\nMessage: {error_message_text}"
        logger.error(msg)
        raise StorageAuthenticationError(msg)
    path = "./aws:AssumeRoleWithWebIdentityResult/aws:Credentials/aws:"
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
        expiration_time = datetime.fromisoformat(
            str(xml_expiration.text).replace("Z", "+00:00")
        )
    except ValueError as error:
        msg = (
            f"Expiration '{xml_expiration.text}' from XML response cannot be parsed "
            f"to a datetime:\n{str(error)}"
        )
        raise StorageAuthenticationError(msg) from error
    expiration_time_in_seconds = (expiration_time - now).total_seconds()

    return CredentialInfo(
        issue_timestamp=now,
        credentials=credentials,
        expiration_time_in_seconds=expiration_time_in_seconds,
    )


async def obtain_credential_info_from_rest_api() -> CredentialInfo:
    now = datetime.now(timezone.utc)
    access_token = await get_access_token()
    response = requests.post(
        url=get_blob_adapter_config().endpoint_url,
        params={
            "Action": "AssumeRoleWithWebIdentity",
            "DurationSeconds": str(get_blob_adapter_config().access_duration),
            "WebIdentityToken": access_token,
            "Version": "2011-06-15", # must be exactly this value
        },
        verify=get_config().hd_adapters_verify_certs,
        auth=None,
        timeout=get_config().external_request_timeout,
    )
    if response.status_code != 200:
        msg = (
            f"BLOB storage credential request returned with status code {response.status_code} "
            f"and response text:\n{response.text}\n"
            f"When calling URL:\n{get_blob_adapter_config().endpoint_url}\n"
        )
        logger.error(msg)
        raise StorageAuthenticationError(msg)

    credential_info = parse_credential_info_from_xml_string(response.text, now)

    return credential_info


def credentials_still_valid_enough(credential_info: CredentialInfo) -> bool:
    now = datetime.now(timezone.utc)

    time_since_issue_in_seconds = (
        now - credential_info.issue_timestamp
    ).total_seconds()

    return (
        time_since_issue_in_seconds <= credential_info.expiration_time_in_seconds * 0.9
    )


async def obtain_or_refresh_credential_info(
    existing_credential_info: CredentialInfo | None = None,
) -> CredentialInfo:
    if existing_credential_info is not None:
        if credentials_still_valid_enough(existing_credential_info):
            return existing_credential_info
        logger.debug("Credentials will soon expire. Trying to get new credentials.")

    return await obtain_credential_info_from_rest_api()


class CredentialManager:
    _current_credential_info: CredentialInfo | None

    def __init__(self) -> None:
        self._current_credential_info = None
        self._credential_thread_lock = threading.Lock()

    async def _obtain_or_refresh_credential_info(self) -> None:
        credential_info = await obtain_or_refresh_credential_info(
            self._current_credential_info
        )
        with self._credential_thread_lock:
            self._current_credential_info = credential_info

    async def get_credentials(self) -> Credentials:
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
    credential_manager = create_or_get_named_credential_manager("blob_adapter_cred")
    credentials = await credential_manager.get_credentials()
    logger.info("Got credentials from credential manager")
    return credentials
