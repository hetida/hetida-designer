import logging
from contextvars import ContextVar
from typing import Any, Dict, List

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasicCredentials, HTTPBearer
from starlette.status import HTTP_403_FORBIDDEN

from hetdesrun.webservice.auth import AuthentificationError, BearerVerifier
from hetdesrun.webservice.config import get_config

logger = logging.getLogger(__name__)

_REQUEST_AUTH_CONTEXT: ContextVar[dict] = ContextVar("_REQUEST_AUTH_CONTEXT")


def set_request_auth_context(value_dict: dict) -> None:
    token = _REQUEST_AUTH_CONTEXT.set(value_dict)
    logger.debug("Request auth context set token: %s", str(token))


def get_request_auth_context() -> dict:
    return _REQUEST_AUTH_CONTEXT.get({})


def get_auth_headers() -> Dict[str, str]:
    """Forward access token when making requests to runtime or adapters"""
    auth_ctx_dict = get_request_auth_context()
    try:
        token = auth_ctx_dict["token"]
    except KeyError:
        possible_fixed_token = get_config().auth_bearer_token_for_external_requests
        if possible_fixed_token is not None:
            logger.debug(
                (
                    "No stored auth token, but explicit token for external requests is present."
                    " Using the explicitely configured token for external requests with schema"
                    " Bearer."
                )
            )
            return {"Authorization": "Bearer " + possible_fixed_token}
        logger.debug("No stored auth token. Not setting auth header")
        return {}
    logger.debug(
        "Found stored auth token. Setting Authorization header with schema Bearer"
    )
    return {"Authorization": "Bearer " + token}


security = HTTPBearer()

bearer_verifier = BearerVerifier.from_verifier_options(
    auth_url=get_config().auth_public_key_url or "",
)


async def has_access(credentials: HTTPBasicCredentials = Depends(security)) -> None:
    """Validate access"""

    if credentials is None:
        logger.info("Unauthorized: Could not obtain credentials from request")

        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Could not obtain credentials from request",
        )

    if not credentials.scheme == "Bearer":  # type: ignore
        logger.info("Unauthorized: No Bearer Schema")
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Wrong authentication method"
        )

    token = credentials.credentials  # type: ignore

    try:
        payload: dict = bearer_verifier.verify_token(token)
        logger.debug("Bearer token payload => %s", payload)
    except AuthentificationError as e:
        raise HTTPException(  # pylint: disable=raise-missing-from
            status_code=401, detail=str(e)
        )
    # Check role
    try:
        if get_config().auth_allowed_role is not None and (
            not get_config().auth_allowed_role in payload[get_config().auth_role_key]
        ):
            # roles are expected in "groups" key in payload
            logger.info("Unauthorized: Roles not allowed")
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Roles not allowed"
            )
    except KeyError:
        logger.info("Unauthorized: No role information in token")
        raise HTTPException(  # pylint: disable=raise-missing-from
            status_code=HTTP_403_FORBIDDEN, detail="No role information in token"
        )

    auth_context_dict = {"token": token, "creds": credentials}
    set_request_auth_context(auth_context_dict)

    logger.debug("Auth token check successful.")


def get_auth_deps() -> List[Any]:
    """Return the authentication dependencies based on the application settings."""
    return [Depends(has_access)] if get_config().auth else []
