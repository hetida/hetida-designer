"""Verfication of requests from designer backend"""

from hetdesrun.auth.keycloak import KeycloakBearerVerifier

from hetdesrun.webservice.config import get_config

kc_bearer_verifier = KeycloakBearerVerifier.from_creds(
    auth_url=get_config().hd_keycloak_auth_url or "",
    realm=get_config().hd_keycloak_realm or "",
    audience=get_config().hd_keycloak_runtime_audience,
)
