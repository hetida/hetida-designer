from typing import Optional, List, Any

import logging


from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from fastapi import HTTPException, Depends

from starlette.status import HTTP_403_FORBIDDEN
from starlette.requests import Request


from hetdesrun.auth.keycloak import AuthentificationError
from hetdesrun.auth.designer import kc_bearer_verifier

from hetdesrun.webservice.config import runtime_config

logger = logging.getLogger(__name__)


class KeycloakJWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[dict]:  # type: ignore
        credentials: Optional[HTTPAuthorizationCredentials] = await super().__call__(
            request
        )

        if credentials is None:
            logger.info("Unauthorized: Could not obtain credentials from request")

            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail="Could not obtain credentials from request",
            )

        if not credentials.scheme == "Bearer":
            logger.info("Unauthorized: No Bearer Schema")
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Wrong authentication method"
            )

        jwt_token = credentials.credentials
        try:
            token_info: dict = kc_bearer_verifier.verify_token(jwt_token)
        except AuthentificationError as e:
            logger.info("Unauthorized: Auth failed: %s", str(e))

            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Invalid bearer token"
            ) from e
        return token_info


hd_auth_dep = KeycloakJWTBearer()


def get_auth_deps() -> List[Any]:
    return [Depends(hd_auth_dep)] if runtime_config.hd_auth_use_keycloak else []
