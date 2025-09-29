import logging

from hetdesrun.webservice.auth_dependency import get_request_auth_context
from hetdesrun.webservice.config import get_config

logger = logging.getLogger(__name__)


def get_runtime_engine_url() -> str:
    """Obtain runtime engine url respecting settings and token roles

    Depending on config the runtime engine url may depend on roles provided
    with the auth token. This function provides the correct runtime engine url
    according to all configuration settings and the current auth token content.

    Note that it falls back to the hd_runtime_engine_url config setting if auth is
    deactivated or if no role is found in the token that maps to another runtime engine url.

    In particular if different urls represent different privileges the hd_runtime_engine_url
    setting should point to the least privileged runtime service!
    """
    role_to_runtime_engine_url_mapping = get_config().auth_runtime_engine_url_by_role

    if (
        role_to_runtime_engine_url_mapping is None
        or len(role_to_runtime_engine_url_mapping.root) == 0
        or not get_config().auth
    ):
        logger.debug("No auth or role mapping not configured: Use default runtime engine url.")
        return get_config().hd_runtime_engine_url

    token_roles_key = get_config().auth_role_key

    auth_context = get_request_auth_context()

    if not "payload" in auth_context:
        msg = "Auth active, but no token in auth context!"
        logger.error(msg)
        raise KeyError(msg)

    token_paylod = get_request_auth_context()["payload"]

    if not get_config().auth_role_key in token_paylod:
        msg = (
            "Auth active and role to runtime engine mapping set, but roles key"
            f" {token_roles_key} not present in token!"
        )
        logger.error(msg)
        raise KeyError(msg)

    roles = token_paylod[token_roles_key]

    if not isinstance(roles, list):
        msg = (
            "Auth active and role to runtime engine mapping set, but roles field"
            f" {token_roles_key} in token is not an array!"
        )
        logger.error(msg)
        raise KeyError(msg)

    for role in roles:
        if role in role_to_runtime_engine_url_mapping.root:
            logger.debug("Found role %s in role to runtime engine mapping", role)
            return role_to_runtime_engine_url_mapping.root[role]

    msg = (
        "Auth active and role to runtime engine mapping set, but could not find a role in"
        " token that matches a key of the mapping. Falling back to default runtime engine url."
    )
    logger.warning(msg)

    return get_config().hd_runtime_engine_url
