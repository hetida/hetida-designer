import logging
import threading
from datetime import datetime, timezone
from functools import cache
from typing import Dict, Optional

import requests
from pydantic import BaseModel, Field

from hetdesrun.adapters.blob_storage.config import get_blob_adapter_config
from hetdesrun.adapters.blob_storage.exceptions import NoAccessTokenAvailable
from hetdesrun.webservice.auth_dependency import (
    forward_request_token_or_get_fixed_token_auth_headers,
)
from hetdesrun.webservice.auth_outgoing import create_or_get_named_access_token_manager
from hetdesrun.webservice.config import ExternalAuthMode, get_config

logger = logging.getLogger(__name__)


class StorageAuthenticationError(Exception):
    """Errors around obtaining and refreshing credentials from Storage"""


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


def obtain_credential_info_from_rest_api(access_token: str) -> CredentialInfo:
    now = datetime.now(timezone.utc)
    response = requests.post(
        url=get_blob_adapter_config().endpoint_url,
        params={
            "Action": "AssumeRoleWithWebIdentity",
            "DurationSeconds": str(get_blob_adapter_config().access_duration),
            "WebIdentityToken": access_token,
            "Version": "2011-06-15",
        },
        verify=get_config().hd_adapters_verify_certs,
        auth=None,
        timeout=get_config().external_request_timeout,
    )
    if response.status_code >= 300:
        msg = (
            f"BLOB storage credential request returned with status code {response.status_code} "
            f"and response text:\n{response.text}\n"
            f"When calling URL:\n{get_blob_adapter_config().endpoint_url}\n"
            f"with access token:\n{access_token}"
        )
        logger.error(msg)
        raise StorageAuthenticationError(msg)

    try:
        response_json = response.json()
    except requests.exceptions.JSONDecodeError as error:
        logger.error(
            "Error decoding response as json:\n%s\nResponse text was:\n%s",
            error,
            response.text,
        )
        raise error

    credentials_json = response_json["AssumeRoleWithWebIdentityResult"]["Credentials"]

    credentials = Credentials(
        access_key_id=credentials_json["AccessKeyId"],
        secret_access_key=credentials_json["SecretAccessKey"],
        session_token=credentials_json["SessionToken"],
    )
    logger.info(
        "Received credentials with expiration %s requested %s",
        credentials_json["Expiration"],
        now.isoformat(),
    )

    return CredentialInfo(
        issue_timestamp=now,
        credentials=credentials,
        expiration_time_in_seconds=get_blob_adapter_config().access_duration,
    )


def credentials_still_valid_enough(credential_info: CredentialInfo) -> bool:
    now = datetime.now(timezone.utc)

    time_since_issue_in_seconds = (
        now - credential_info.issue_timestamp
    ).total_seconds()

    return (
        time_since_issue_in_seconds <= credential_info.expiration_time_in_seconds * 0.9
    )


def obtain_or_refresh_credential_info(
    access_token: str, existing_credential_info: Optional[CredentialInfo] = None
) -> CredentialInfo:
    if existing_credential_info is not None:
        if credentials_still_valid_enough(existing_credential_info):
            return existing_credential_info
        logger.debug("Credentials will soon expire. Trying to get new credentials.")

    try:
        return obtain_credential_info_from_rest_api(access_token)
    except StorageAuthenticationError as error:
        logger.error("Obtaining new credentails failed:\n%s", str(error))
        raise error


class CredentialManager:
    _current_credential_info: Optional[CredentialInfo]

    def __init__(self, access_token: str):
        self.access_token = access_token
        self._current_credential_info = None
        self._credential_thread_lock = threading.Lock()

    def _obtain_or_refresh_credential_info(self) -> None:
        credential_info = obtain_or_refresh_credential_info(
            self.access_token, self._current_credential_info
        )
        with self._credential_thread_lock:
            self._current_credential_info = credential_info

    def get_credentials(self) -> Credentials:
        self._obtain_or_refresh_credential_info()
        assert self._current_credential_info is not None
        return self._current_credential_info.credentials


@cache
def global_credential_manager_dict() -> Dict[str, CredentialManager]:
    return {}


def create_or_get_named_credential_manager(
    key: str, access_token: Optional[str]
) -> CredentialManager:
    manager_dict = global_credential_manager_dict()

    if key in manager_dict:
        return manager_dict[key]

    logger.info("Creating new credential manager for key %s", key)

    if access_token is None:
        msg = (
            "Access token has to be specified at least the first time"
            " the credential manager is requested!"
        )
        logger.error(msg)
        raise ValueError(msg)

    manager_dict[key] = CredentialManager(access_token=access_token)

    return manager_dict[key]


def get_access_token() -> str:
    external_mode = get_config().external_auth_mode
    if external_mode == ExternalAuthMode.OFF:
        msg = (
            "Config option external_auth_mode is set to 'OFF' "
            "thus no access token is available!"
        )
        logger.error(msg)
        raise NoAccessTokenAvailable(msg)
    if external_mode == ExternalAuthMode.FORWARD_OR_FIXED:
        token_header = forward_request_token_or_get_fixed_token_auth_headers()
        access_token = token_header["Authorization"].split("Bearer ")[-1]
        return access_token
    if external_mode == ExternalAuthMode.CLIENT:
        service_credentials = get_config().external_auth_client_credentials
        assert service_credentials is not None  # for mypy
        access_token_manager = create_or_get_named_access_token_manager(
            "outgoing_external_auth", service_credentials
        )
        access_token = access_token_manager.sync_get_access_token()
        return access_token

    msg = (
        f"Unknown config option for external_auth_mode '{external_mode}' "
        "thus no access token is available!"
    )
    logger.error(msg)
    raise NoAccessTokenAvailable(msg)


def get_credentials() -> Credentials:
    credential_manager = create_or_get_named_credential_manager(
        "blob_adapter_cred", get_access_token()
    )
    credentials = credential_manager.get_credentials()
    logger.info("Got credentials from credential manager")
    return credentials
