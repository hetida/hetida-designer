"""Verfication of requests from designer backend"""

from hetdesrun.auth.keycloak import KeycloakBearerVerifier

from hetdesrun.service.config import runtime_config

kc_bearer_verifier = KeycloakBearerVerifier.from_creds(
    auth_url=runtime_config.hd_keycloak_auth_url or "",
    realm=runtime_config.hd_keycloak_realm or "",
    audience=runtime_config.hd_keycloak_runtime_audience,
)
