"""Management of access token for making external requests to other services

This provides classes and functions for obtaining, handling and managing
access tokens as well as token refresh for tokens provided by an openidconnect
auth provider, e.g. keycloak.
"""

import asyncio
import datetime
import json
import logging
import threading
from enum import Enum
from functools import cache
from posixpath import join as posix_urljoin
from typing import Any, Literal

from httpx import AsyncClient, HTTPError, Response
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)


def json_serialize_dt(obj: datetime.datetime | datetime.date) -> str:
    """JSON serializer including datetime objects

    usage: json.dumps(my_object, default=json_serialize_dt)
    """

    if isinstance(obj, datetime.datetime | datetime.date):
        return obj.isoformat()
    raise TypeError(f"Type {str(type(obj))} not json serializable")


class ServiceAuthenticationError(Exception):
    """Errors around obtaining and refreshing access tokens from auth provider"""


class PasswordGrantCredentials(BaseModel):
    grant_type: Literal["password"] = "password"
    username: str
    password: str
    client_id: str
    client_secret: str | None = None


class ClientCredentialsGrantCredentials(BaseModel):
    grant_type: Literal["client_credentials"] = "client_credentials"
    client_id: str
    client_secret: str


class ServiceCredentials(BaseModel):
    """Bundles auth setup information together with the grant credentials"""

    realm: str
    auth_url: str
    audience: str | None = Field("account")
    grant_credentials: PasswordGrantCredentials | ClientCredentialsGrantCredentials
    post_client_kwargs: dict[str, Any] = Field(
        {},
        description=(
            "Additional keyword arguments for httpx AsyncClient against auth provider."
            " Affects both obtaining and refreshing requests."
        ),
        example={"verify": False},
    )
    post_kwargs: dict[str, Any] = Field(
        {},
        description=(
            "Additional keyword arguments for httpx post requests against auth provider."
            " Affects both obtaining and refreshing requests."
        ),
        example={"timeout": 42.0},
    )


class TokenType(str, Enum):
    """Supported token types"""

    bearer = "bearer", str, "Bearer", "BEARER"

    def __new__(cls, *values: Any) -> "TokenType":
        obj = str.__new__(cls, values[0])  #  type: ignore

        # first value is canonical value (e.g. what you get when calling TokenType.bearer.value)
        obj._value_ = values[0]

        cls.parse_type: type  # for mypy # noqa: B032
        obj.parse_type = values[1]  # set parse_type to second tuple entry

        for other_value in values[2:]:
            # register other values in order to allow initializations TokenType("Bearer")
            # and TokenType("BEARER") to work. This uses an internal attribute of Enum!

            cls._value2member_map_[other_value] = obj  # type: ignore

        obj._all_values = (values[0],) + values[1:]  # type: ignore
        return obj  # type:ignore


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None  # client credential grants don't provide refreh token
    expires_in: int
    refresh_expires_in: int = 0
    token_type: TokenType
    not_before_policy: int = Field(
        ...,
        alias="not-before-policy",
        le=0,
        description="Expect tokens to be usable immediately!",
    )
    session_state: str = ""
    scope: str
    issue_timestamp: datetime.datetime = Field(
        ...,
        description=(
            "UTC zoned timestamp shortly before requesting token."
            " Is used to calculate expiration time estimates."
        ),
    )

    class Config:
        allow_population_by_field_name = True


def json_parse_token_response(resp: Response) -> dict[str, Any]:
    try:
        resp_dict: dict[str, Any] = resp.json()
        return resp_dict
    except json.JSONDecodeError as e:
        msg = "Error trying to json-parse token response from auth provider"
        logger.error(msg)
        raise ServiceAuthenticationError(
            msg + " Json decode error was:\n" + str(e) + "\n\nResponse text was:\n" + resp.text
        ) from e


async def post_to_auth_provider(
    url: str,
    data: dict[str, Any],
    async_client_kwargs: dict[str, Any],
    post_kwargs: dict[str, Any],
) -> Response:
    async with AsyncClient(**(async_client_kwargs)) as client:  # noqa: S113
        resp = await client.post(
            url=url,
            data=data,
            **(post_kwargs),
        )
    return resp


async def obtain_token_from_auth_provider(
    service_user_credentials: ServiceCredentials,
) -> TokenResponse:
    """Obtain token via the appropriate grant type

    Raises:
        ServiceAuthenticationError - in case of connection problems or invalid credentials
    """

    now = datetime.datetime.now(datetime.timezone.utc)
    url = posix_urljoin(
        service_user_credentials.auth_url,
        "realms",
        service_user_credentials.realm,
        "protocol/openid-connect/token",
    )

    try:
        resp = await post_to_auth_provider(
            url=url,
            data=service_user_credentials.grant_credentials.dict(exclude_none=True),
            async_client_kwargs=service_user_credentials.post_client_kwargs,
            post_kwargs=service_user_credentials.post_kwargs,
        )
    except HTTPError as e:
        msg = f"Error trying to get token from auth provider at {url}."
        logger.error(msg)
        raise ServiceAuthenticationError(msg + " Http error was:\n" + str(e)) from e

    token_dict = json_parse_token_response(resp)
    token_dict["issue_timestamp"] = now

    try:
        token_response = TokenResponse.parse_obj(token_dict)
    except ValidationError as e:
        msg = (
            f"Could not understand answer to token request from auth provider at"
            f" {url}. token dict:\n"
            f"{json.dumps(token_dict, indent=2, default=json_serialize_dt)}"
        )
        logger.error(msg)
        raise ServiceAuthenticationError(msg + "\nError was:\n" + str(e)) from e

    return token_response


async def refresh_token_from_auth_provider(
    refresh_token: str, service_user_credentials: ServiceCredentials
) -> TokenResponse:
    """Refresh token using the provided refresh token

    Raises:
        ServiceAuthenticationError - in case of connection problems or invalid credentials
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    url = posix_urljoin(
        service_user_credentials.auth_url,
        "realms",
        service_user_credentials.realm,
        "protocol/openid-connect/token",
    )

    try:
        resp = await post_to_auth_provider(
            url=url,
            data={
                "client_id": service_user_credentials.grant_credentials.client_id,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            async_client_kwargs=service_user_credentials.post_client_kwargs,
            post_kwargs=service_user_credentials.post_kwargs,
        )
    except HTTPError as e:
        msg = f"Error trying to refresh token from auth provider at {url}."
        logger.error(msg)
        raise ServiceAuthenticationError(msg + " Http error was:\n" + str(e)) from e

    token_dict = json_parse_token_response(resp)

    token_dict["issue_timestamp"] = now

    try:
        token_response = TokenResponse.parse_obj(token_dict)
    except ValidationError as e:
        msg = (
            f"Could not understand answer to token refresh request from auth provider at"
            f" {url}. token dict:\n"
            f"{json.dumps(token_dict, indent=2, default=json_serialize_dt)}"
        )
        logger.error(msg)
        raise ServiceAuthenticationError(msg + "\nError was:\n" + str(e)) from e

    return token_response


def access_token_still_valid_enough(token_info: TokenResponse) -> bool:
    """Checks whether access token expiration may still allow making requests with it"""
    now = datetime.datetime.now(datetime.timezone.utc)

    time_since_issue_in_seconds = (now - token_info.issue_timestamp).total_seconds()

    return time_since_issue_in_seconds <= token_info.expires_in * 0.9


def should_try_refresh(token_info: TokenResponse) -> bool:
    """Checks both tokens' expirations whether a refresh is desirable"""
    if token_info.refresh_token is None:
        logger.debug("No refresh token found in token info.")
        return False
    now = datetime.datetime.now(datetime.timezone.utc)

    time_since_issue_in_seconds = (now - token_info.issue_timestamp).total_seconds()

    return (time_since_issue_in_seconds > token_info.expires_in * 0.9) and (
        time_since_issue_in_seconds + 10 < token_info.refresh_expires_in
    )


async def obtain_or_refresh_token(
    service_user_credentials: ServiceCredentials,
    existing_token_info: TokenResponse | None = None,
) -> TokenResponse:
    """Logic for actually doing token obtaining and refreshs

    If access token is still valid enough, it is returned as is.
    If not, this tries to refresh using the refresh token if its expiration is
    far enough in the future. If that is not the case or the refresh fails it falls back
    to obtaining a completely new token set instead.

    Raises:
        ServiceAuthenticationError - If nothing works out and no new / valid
            token can be obtained

    """

    if existing_token_info is not None:
        if access_token_still_valid_enough(existing_token_info):
            return existing_token_info

        logger.debug("Access token not fresh enough. Trying to update.")
        if should_try_refresh(existing_token_info):
            assert (  # noqa: S101
                existing_token_info.refresh_token is not None
            )  # for mypy
            logger.debug("Refresh token fresh enough. Trying to update from refresh token")
            try:
                return await refresh_token_from_auth_provider(
                    existing_token_info.refresh_token, service_user_credentials
                )
            except ServiceAuthenticationError as e:
                logger.error(
                    "Token refresh failed: %s. Trying to get completely new tokens.",
                    str(e),
                )
                try:
                    return await obtain_token_from_auth_provider(service_user_credentials)
                except ServiceAuthenticationError as e2:
                    logger.error(
                        (
                            "After failed refresh also obtaining completely new"
                            " tokens failed:\n%s."
                        ),
                        str(e2),
                    )
                    raise e2
        logger.debug("Both tokens not fresh enough. Try to get completely new tokens.")
        try:
            return await obtain_token_from_auth_provider(service_user_credentials)
        except ServiceAuthenticationError as e:
            # for some reason the existing token does not work or refresh does not work
            logger.error(
                "Both tokens where not fresh enough but obtaining new tokens failed: %s",
                str(e),
            )
            raise e

    return await obtain_token_from_auth_provider(service_user_credentials)


class AccessTokenManager:
    """Management of access token and refresh token

    Refreshs access token from refresh token if necessary.

    Stores token info across threads in order to reduce number of necessary
    requests to auth provider.

    Note: Does not manage tokens across processes in a multiprocessing setup.
    """

    _current_token_info: TokenResponse | None

    def __init__(self, creds: ServiceCredentials):
        self.creds = creds
        self._current_token_info = None
        self._token_thread_lock = threading.Lock()
        self._token_async_lock = asyncio.Lock()

    async def _obtain_or_refresh_token_info(self) -> None:
        token_info = await obtain_or_refresh_token(self.creds, self._current_token_info)
        with self._token_thread_lock:
            self._current_token_info = token_info

    async def get_access_token(self) -> str:
        """Provides a valid access token"""
        async with self._token_async_lock:
            await self._obtain_or_refresh_token_info()
        assert self._current_token_info is not None  # for mypy # noqa: S101
        return self._current_token_info.access_token

    def sync_get_access_token(self) -> str:
        """Synchronous wrapper for providing a valid access token

        Use this if you do are not in an async environment.
        """
        return asyncio.run(self.get_access_token())


##### Access token Managers
# Some support for managing multiple "global" access token manager objects
# for different purposes:


@cache
def global_access_token_manager_dict() -> dict[str, AccessTokenManager]:
    return {}


def create_or_get_named_access_token_manager(
    key: str, creds: ServiceCredentials | None = None
) -> AccessTokenManager:
    """Create/get global access token manager

    At least on the first call for any key, creds have to be provided. The access token
    manager is then cached via the provided key.

    At subsequent invocations only the key is required and eventually provided creds
    are ignored. So it is okay, to always call with both.

    """
    manager_dict = global_access_token_manager_dict()

    if key in manager_dict:
        return manager_dict[key]

    logger.debug("Creating new access token manager for key %s", key)
    if creds is None:
        raise ValueError(
            "Credentials have to be specified at least the first time the"
            " access token manager is requested"
        )

    manager_dict[key] = AccessTokenManager(creds=creds)

    return manager_dict[key]
