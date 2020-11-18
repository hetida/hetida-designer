"""Keycloak auth utilities

Provides some basic functionality for authentification against Keycloak.

This is used to verify requests from designer backend if keycloak authentification
is enabled. Furthermore it provides basic handling of access tokens which can be
used by adapter implementations.
"""


from typing import Optional

from posixpath import join as posix_urljoin

from enum import Enum

import datetime

import logging

import threading

from requests import get, post, HTTPError

from jose import jwt, JOSEError

from pydantic import (  # pylint: disable=no-name-in-module
    BaseModel,
    Field,
    ValidationError,
)

logger = logging.getLogger(__name__)


class AuthentificationError(Exception):
    pass


class ServiceUserCredentials(BaseModel):
    realm: str
    client_id: str
    username: str
    password: str
    auth_url: str
    audience: Optional[str] = Field("account")


class TokenType(str, Enum):
    """We only accept bearer tokens for now"""

    bearer = "bearer"


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    refresh_expires_in: int
    token_type: TokenType
    not_before_policy: int = Field(
        ...,
        alias="not-before-policy",
        le=0,
        description="Runtime expects tokens to be usable immediately!",
    )
    session_state: str
    scope: str
    issue_timestamp: datetime.datetime


def obtain_token_from_keycloak(
    service_user_credentials: ServiceUserCredentials,
) -> TokenResponse:

    now = datetime.datetime.utcnow()
    try:
        resp = post(
            url=posix_urljoin(
                service_user_credentials.auth_url,
                "realms",
                service_user_credentials.realm,
                "protocol/openid-connect/token",
            ),
            data={
                "client_id": service_user_credentials.client_id,
                "username": service_user_credentials.username,
                "password": service_user_credentials.password,
                "grant_type": "password",
            },
        )
    except HTTPError as e:
        logger.info("Error trying to get token from Keycloak")
        raise AuthentificationError(
            "Error trying to get token from Keycloak: " + str(e)
        ) from e

    token_dict = resp.json()
    token_dict["issue_timestamp"] = now

    try:
        token_response = TokenResponse.parse_obj(token_dict)
    except ValidationError as e:
        logger.info("Could not understand answer to token request from keycloak")
        raise AuthentificationError(
            "Could not understand answer to token request from keycloak"
        ) from e

    return token_response


def refresh_token_from_keycloak(
    refresh_token: str, service_user_credentials: ServiceUserCredentials
) -> TokenResponse:
    now = datetime.datetime.utcnow()
    try:
        resp = post(
            url=posix_urljoin(
                service_user_credentials.auth_url,
                "realms",
                service_user_credentials.realm,
                "protocol/openid-connect/token",
            ),
            data={
                "client_id": service_user_credentials.client_id,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
        )
    except HTTPError as e:
        logger.info("Error trying to refresh token from Keycloak")
        raise AuthentificationError("Error trying to get token from Keycloak") from e

    token_dict = resp.json()
    token_dict["issue_timestamp"] = now

    try:
        token_response = TokenResponse.parse_obj(token_dict)
    except ValidationError as e:
        logger.info(
            "Could not understand answer to token refresh request from keycloak"
        )
        raise AuthentificationError(
            "Could not understand answer to token request from keycloak"
        ) from e

    return token_response


def access_token_still_valid_enough(token_info: TokenResponse) -> bool:
    now = datetime.datetime.utcnow()

    time_since_issue_in_seconds = (now - token_info.issue_timestamp).total_seconds()

    return time_since_issue_in_seconds <= token_info.expires_in * 0.9


def should_try_refresh(token_info: TokenResponse) -> bool:
    now = datetime.datetime.utcnow()

    time_since_issue_in_seconds = (now - token_info.issue_timestamp).total_seconds()

    return (time_since_issue_in_seconds > token_info.expires_in * 0.9) and (
        time_since_issue_in_seconds + 10 < token_info.refresh_expires_in
    )


def obtain_or_refresh_token(
    service_user_credentials: ServiceUserCredentials,
    existing_token_info: Optional[TokenResponse] = None,
) -> TokenResponse:
    if existing_token_info is not None:
        try:
            if access_token_still_valid_enough(existing_token_info):
                return existing_token_info
            if should_try_refresh(existing_token_info):
                return refresh_token_from_keycloak(
                    existing_token_info.refresh_token, service_user_credentials
                )
            raise AuthentificationError("Token state unclear")
        except AuthentificationError:
            # for some reason the existing token does not work or refresh does not work
            return obtain_token_from_keycloak(service_user_credentials)
    return obtain_token_from_keycloak(service_user_credentials)


class KeycloakAccessTokenManager:
    """Simple Management of keycloak access token

    Refreshs access token from refresh token if necessary.

    Stores token info across threads in order to reduce number of necessary
    requests to keycloak.
    """

    def __init__(self, creds: ServiceUserCredentials):
        self.creds = creds
        self._current_token_info: Optional[TokenResponse] = None
        self._keycloak_token_lock = threading.Lock()

    def _obtain_or_refresh_token_info(self) -> None:
        if self._current_token_info is not None:
            try:
                if not access_token_still_valid_enough(self._current_token_info):
                    if should_try_refresh(self._current_token_info):
                        logger.debug("Renewing Token from Refresh Token")
                        with self._keycloak_token_lock:
                            self._current_token_info = refresh_token_from_keycloak(
                                self._current_token_info.refresh_token, self.creds
                            )
                    else:
                        logger.debug("Renewing Token completely (both tokens invalid)")
                        with self._keycloak_token_lock:
                            self._current_token_info = obtain_token_from_keycloak(
                                self.creds
                            )
            except AuthentificationError:
                # for some reason the existing token does not work or refresh does not work
                with self._keycloak_token_lock:
                    self._current_token_info = obtain_token_from_keycloak(self.creds)

        else:
            with self._keycloak_token_lock:
                self._current_token_info = obtain_token_from_keycloak(self.creds)

    def get_access_token(self) -> str:
        """Provides a valid access token"""
        self._obtain_or_refresh_token_info()
        assert self._current_token_info is not None  # for mypy
        return self._current_token_info.access_token


# Public Key Bearer token verification


class KeycloakBearerVerifierCredentials(BaseModel):
    auth_url: str
    realm: str
    audience: Optional[str] = Field("account")


class KeycloakBearerVerifier:
    def __init__(self, creds: KeycloakBearerVerifierCredentials):
        self.creds = creds
        self._keycloak_public_key_data = None
        self._keycloak_public_key_lock = threading.Lock()

    @classmethod
    def from_creds(
        cls, auth_url: str, realm: str, audience: Optional[str] = "account"
    ) -> "KeycloakBearerVerifier":
        return cls(
            KeycloakBearerVerifierCredentials(
                auth_url=auth_url, realm=realm, audience=audience
            )
        )

    def verify_token(self, access_token: str) -> dict:
        self._obtain_public_key_data()
        try:
            decoded_bearer_token: dict = jwt.decode(
                access_token,
                self._keycloak_public_key_data,
                audience=self.creds.audience,
            )
        except JOSEError as e:  # this is the base exception class of jose
            logger.info(
                "Failing to verify Bearer Token: %s\nError: %s", access_token, str(e)
            )
            raise AuthentificationError("Failed to verify Bearer Token") from e
        return decoded_bearer_token

    def _obtain_public_key_data(self) -> None:
        if self._keycloak_public_key_data is not None:
            # assume public key is not rotated and therefore valid forever
            return
        url = posix_urljoin(
            self.creds.auth_url,
            "realms",
            self.creds.realm,
            "protocol/openid-connect/certs",
        )
        try:
            resp = get(url)
        except HTTPError as e:
            logger.info("Error trying to get public key from Keycloak: %s", str(e))
            raise AuthentificationError(
                "Error trying to get public key from Keycloak"
            ) from e
        with self._keycloak_public_key_lock:
            self._keycloak_public_key_data = resp.json()
