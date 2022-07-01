# pylint: disable=duplicate-code

from typing import Dict

from hetdesrun.auth.keycloak import (
    KeycloakAccessTokenManager,
    ServiceUserCredentials,
)

from hetdesrun.webservice.config import runtime_config

# get creds from config

generic_rest_kc_access_token_manager = (
    KeycloakAccessTokenManager(
        creds=ServiceUserCredentials(
            realm=runtime_config.hd_generic_rest_adapter_keycloak_realm,
            client_id=runtime_config.hd_generic_rest_adapter_keycloak_runtime_client_id,
            username=runtime_config.hd_generic_rest_adapter_keycloak_runtime_username,
            password=runtime_config.hd_generic_rest_adapter_keycloak_runtime_password,
            auth_url=runtime_config.hd_generic_rest_adapter_keycloak_auth_url,
            audience=runtime_config.hd_generic_rest_adapter_keycloak_runtime_audience,
        )
    )
    if runtime_config.hd_generic_rest_adapter_auth_use_keycloak
    else None
)


def get_generic_rest_adapter_auth_headers() -> Dict[str, str]:
    return (
        {
            "Authorization": "Bearer "
            + generic_rest_kc_access_token_manager.get_access_token()
        }
        if generic_rest_kc_access_token_manager is not None
        else {}
    )
