import logging
import threading
from datetime import datetime, timezone
from functools import cache
from typing import Dict, Optional

import boto3
from pydantic import BaseModel, Field

from hetdesrun.adapters.blob_storage.config import get_blob_adapter_config
from hetdesrun.webservice.auth_outgoing import create_or_get_named_access_token_manager
from hetdesrun.webservice.config import get_config

logger = logging.getLogger(__name__)


class StsAuthenticationError(Exception):
    """Errors around obtaining and refreshing credentials from STS"""


class Credentials(BaseModel):
    access_key_id: str
    secret_access_key: str
    session_token: str


def obtain_credentials_from_sts(access_token: str):
    sts_client = boto3.client(
        "sts",
        region_name=get_blob_adapter_config().region_name,
        use_ssl=False,
        endpoint_url=get_blob_adapter_config().endpoint_url,
    )

    response = sts_client.assume_role_with_web_identity(
        # Amazon Resource Name (ARN)
        # arn:partition:service:region:account-id:(resource-type/)resource-id
        RoleArn=(
            f"arn:aws:iam::{get_blob_adapter_config().account_id}"
            f":{get_blob_adapter_config().resource_id}"
        ),
        RoleSessionName="get-credentials",
        WebIdentityToken=access_token,
        DurationSeconds=get_blob_adapter_config().access_duration,
    )

    credentials_json = response["Credentials"]

    credentials = Credentials(
        access_key_id=credentials_json["AccessKeyId"],
        secret_access_key=credentials_json["SecretAccessKey"],
        session_token=credentials_json["SessionToken"],
    )

    return credentials


class CredentialResponse(BaseModel):
    credentials: Credentials
    issue_timestamp: datetime = Field(
        ...,
        description=(
            "UTC zoned timestamp shortly before requesting token."
            " Is used to calculate expiration time estimates."
        ),
    )
    expiration_time_in_seconds: int


def credentials_still_valid_enough(credential_info: CredentialResponse) -> bool:
    now = datetime.now(timezone.utc)

    time_since_issue_in_seconds = (
        now - credential_info.issue_timestamp
    ).total_seconds()

    return (
        time_since_issue_in_seconds <= credential_info.expiration_time_in_seconds * 0.9
    )


def obtain_or_refresh_credentials(
    access_token: str, existing_credential_info: Optional[CredentialResponse] = None
) -> CredentialResponse:
    if existing_credential_info is not None:
        if credentials_still_valid_enough(existing_credential_info):
            return existing_credential_info
        logger.debug("Credentials will soon expire. Trying to get new credentials.")

    try:
        return obtain_credentials_from_sts(access_token)
    except StsAuthenticationError as error:
        logger.error("Obtaining new credentails failed:\n%s", str(error))
        raise error


class CredentialManager:
    _current_credential_info: Optional[CredentialResponse]

    def __init__(self, access_token: str):
        self.access_token = access_token
        self._current_credential_info = None
        self._credential_thread_lock = threading.Lock()

    def _obtain_or_refresh_credential_info(self) -> None:
        credential_info = obtain_or_refresh_credentials(
            self.access_token, self._current_credential_info
        )
        with self._credential_thread_lock:
            self._current_credential_info = credential_info

    def get_credentials(self) -> str:
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

    logger.debug("Creating new credential manager for key %s", key)

    if access_token is None:
        raise ValueError(
            "Access token has to be specified at least the first time"
            " the credential manager is requested!"
        )

    manager_dict[key] = CredentialManager(access_token=access_token)


def get_access_token() -> str:
    service_credentials = get_config().internal_auth_client_credentials
    assert service_credentials is not None  # for mypy
    access_token_manager = create_or_get_named_access_token_manager(
        "blob_adapter_auth", service_credentials
    )
    access_token = access_token_manager.sync_get_access_token()
    return access_token


def get_credentials() -> Credentials:
    credential_manager = create_or_get_named_credential_manager(
        "blob_adapter_cred", get_access_token()
    )
    credentials = credential_manager.get_credentials()
    return credentials
