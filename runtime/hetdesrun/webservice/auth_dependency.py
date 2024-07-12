import asyncio
import logging
from contextvars import ContextVar
from typing import Annotated, Any

from fastapi import Cookie, Depends, Header, HTTPException
from fastapi.security import HTTPBasicCredentials, HTTPBearer
from starlette.status import HTTP_403_FORBIDDEN

from hetdesrun.webservice.auth import AuthentificationError, BearerVerifier
from hetdesrun.webservice.auth_outgoing import create_or_get_named_access_token_manager
from hetdesrun.webservice.config import ExternalAuthMode, InternalAuthMode, get_config

logger = logging.getLogger(__name__)

_REQUEST_AUTH_CONTEXT: ContextVar[dict] = ContextVar("_REQUEST_AUTH_CONTEXT")


def set_request_auth_context(value_dict: dict) -> None:
    token = _REQUEST_AUTH_CONTEXT.set(value_dict)
    logger.debug("Request auth context set token: %s", str(token))


def get_request_auth_context() -> dict:
    return _REQUEST_AUTH_CONTEXT.get({})


def forward_request_token_or_get_fixed_token_auth_headers() -> dict[str, str]:
    """Handles the FORWARD_OR_FIXED outgoing auth modes

    If a bearer token was provided with a currently handled ingoing request,
    it will be forwarded, i.e. the corresponding auth header dictionary will be
    returned by this function.

    If that is not the case, the auth_bearer_token_for_outgoing_requests config
    option will be checked and used instead if present.

    Otherwise empty auth header dictionary will be returned.
    """
    auth_ctx_dict = get_request_auth_context()
    try:
        token = auth_ctx_dict["token"]
    except KeyError:
        possible_fixed_token = get_config().auth_bearer_token_for_outgoing_requests
        if possible_fixed_token is not None:
            logger.debug(
                "No stored auth token, but explicit token for outgoing requests is present."
                " Using the explicitely configured token for outgoing requests with schema"
                " Bearer."
            )
            return {"Authorization": "Bearer " + possible_fixed_token}
        logger.debug(
            "No stored auth token and no explititely fixed configured token."
            " Not setting auth header"
        )
        return {}
    logger.debug("Found stored auth token. Setting Authorization header with schema Bearer")
    return {"Authorization": "Bearer " + token}


async def get_auth_headers(external: bool = False) -> dict[str, str]:
    """Auth header dict depending on outgoing request being external/internal

    Obtains auth headers for making an outgoing web request depending on
    * whether the request is internal (backend to runtime)
    * or external (to adapters, importing/exporting from another instance)
    and the corresponding configuration

    returns a dict of headers, either empty or of form
    {"Authorization": "Bearer ...."}

    Params:
        external: Whether the intended request is external (e.g to adapters or for
            export import), or internal (e.g. from backend to runtime)

    Raises:
        hetdesrun.webservice.auth_outgoing.ServiceAuthenticationError - if obtaining
            valid access tokens from auth provider fails somehow.
    """

    if external:
        external_mode = get_config().external_auth_mode
        if external_mode == ExternalAuthMode.OFF:
            return {}
        if external_mode == ExternalAuthMode.FORWARD_OR_FIXED:
            return forward_request_token_or_get_fixed_token_auth_headers()
        if external_mode == ExternalAuthMode.CLIENT:
            service_credentials = get_config().external_auth_client_credentials
            assert service_credentials is not None  # for mypy # noqa: S101
            access_token_manager = create_or_get_named_access_token_manager(
                "outgoing_external_auth", service_credentials
            )
            access_token = await access_token_manager.get_access_token()
            return {"Authorization": "Bearer " + access_token}

        msg = f"Unknown config option for external_auth_mode: {external_mode}"
        logger.error(msg)
        raise ValueError(msg)

    # internal

    internal_mode = get_config().internal_auth_mode
    if internal_mode == InternalAuthMode.OFF:
        return {}
    if internal_mode == InternalAuthMode.FORWARD_OR_FIXED:
        return forward_request_token_or_get_fixed_token_auth_headers()
    if internal_mode == InternalAuthMode.CLIENT:
        service_credentials = get_config().internal_auth_client_credentials
        assert service_credentials is not None  # for mypy # noqa: S101
        access_token_manager = create_or_get_named_access_token_manager(
            "outgoing_internal_auth", service_credentials
        )
        access_token = await access_token_manager.get_access_token()
        return {"Authorization": "Bearer " + access_token}

    msg = f"Unknown config option for internal_auth_mode: {internal_mode}"
    logger.error(msg)
    raise ValueError(msg)


def sync_wrapped_get_auth_headers(external: bool = False) -> dict[str, str]:
    return asyncio.run(get_auth_headers(external=external))


security = HTTPBearer()

bearer_verifier = BearerVerifier.from_verifier_options(
    auth_url=get_config().auth_public_key_url or "",
    verify_ssl=get_config().auth_verify_certs,
)


async def has_access(credentials: HTTPBasicCredentials = Depends(security)) -> None:
    """Validate access"""

    if credentials is None:
        logger.info("Unauthorized: Could not obtain credentials from request")

        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Could not obtain credentials from request",
        )

    if credentials.scheme != "Bearer":  # type: ignore
        logger.info("Unauthorized: No Bearer Schema")
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Wrong authentication method")

    token = credentials.credentials  # type: ignore

    try:
        payload: dict = bearer_verifier.verify_token(token)
        logger.debug("Bearer token payload => %s", payload)
    except AuthentificationError as e:
        raise HTTPException(status_code=401, detail=str(e)) from None
    # Check role
    try:
        if get_config().auth_allowed_role is not None and (
            not get_config().auth_allowed_role in payload[get_config().auth_role_key]
        ):
            # roles are expected in "groups" key in payload
            logger.info("Unauthorized: Roles not allowed")
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Roles not allowed")
    except KeyError:
        logger.info("Unauthorized: No role information in token")
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="No role information in token"
        ) from None

    auth_context_dict = {"token": token, "creds": credentials}
    set_request_auth_context(auth_context_dict)

    logger.debug("Auth token check successful.")


async def is_authenticated_check_no_abort(  # noqa: PLR0911, PLR0912
    Authorization: Annotated[str | None, Header()] = None,
    access_token: Annotated[str | None, Cookie()] = None,
) -> bool:
    """Validate access from header or cookie and allow to react to auth checking

    This does two things:
    * allow access token to come in either header (preferred) or in an "access_token"
      cookie (necessary for auth in dashboarding endpoint)
    * not just throw exceptions but return authentication status (bool) in order
      to allow to react to it in endpoint code. This is also necessary for the dashboard
      endpoint
    """

    if not get_config().auth:
        return True

    # Sort out what to actually check
    if Authorization is not None:
        if Authorization.startswith("Bearer "):
            access_token_to_check = Authorization[7:]
        else:
            logger.warning(
                "Got Authorization header but scheme is different from Bearer."
                " Handling this request as unauthorized even if cookies are provided."
            )
            return False
    else:  # noqa: PLR5501
        if access_token is None:
            logger.info(
                "Neither Authorization header and access_token cookie are provided."
                " Neglecting access."
            )
            return False
        if access_token.startswith("Bearer "):
            access_token_to_check = access_token[7:]
        else:
            access_token_to_check = access_token

    assert access_token_to_check is not None  # noqa: S101

    # Actually checking
    try:
        payload: dict = bearer_verifier.verify_token(access_token_to_check)
        logger.debug("Bearer token payload => %s", payload)
    except AuthentificationError as e:
        logger.debug("Token verification Error: %s", str(e))
        return False

    # Check role
    try:
        if get_config().auth_allowed_role is not None and (
            not get_config().auth_allowed_role in payload[get_config().auth_role_key]
        ):
            # roles are expected in "groups" key in payload
            logger.info("Unauthorized: Roles not allowed")
            return False
    except KeyError:
        logger.info("Unauthorized: No role information in token")
        return False

    # Passed all checks
    auth_context_dict = {"token": access_token_to_check, "creds": None}
    set_request_auth_context(auth_context_dict)
    return True


def get_auth_deps() -> list[Any]:
    """Return the authentication dependencies based on the application settings."""
    return [Depends(has_access)] if get_config().auth else []
