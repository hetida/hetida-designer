import datetime
import json
import logging
import threading
from typing import cast

import httpx
from joserfc import jwt
from joserfc.errors import JoseError
from joserfc.jwk import JWKRegistry, KeySet, KeySetSerialization
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AuthentificationError(Exception):
    pass


# Options steering claims validation. Signature verification is always performed
# by joserfc and cannot be disabled. Expiration (exp) and not-before (nbf) timestamps
# are validated whenever the respective claim is present in the token; "require_exp"
# additionally makes a missing exp claim an error, since a token without expiration
# should not be accepted. If an expected audience / issuer is configured, the
# respective claim must be present in the token and match — a token lacking the
# claim is rejected.
DEFAULT_OPTIONS = {
    "verify_aud": True,
    "verify_iss": True,
    "require_exp": True,
}

# Asymmetric JWT signature algorithms accepted by default. Only asymmetric algorithms
# may be listed here. These cover the algorithms commonly offered by OpenID Connect providers such
# as Keycloak.
DEFAULT_ALLOWED_ALGORITHMS = ["RS256", "RS384", "RS512", "ES256", "ES384", "ES512"]


class FrontendAuthOptions(BaseModel):
    """For html backends using keycloak-js

    These options may be injected into a html website generated including
    keycloak-js setup.
    """

    auth_url: str = Field("", description="Base auth url as required by keycloak-js.")
    realm: str = ""
    client_id: str = ""


class BearerVerifierOptions(BaseModel):
    auth_url: str
    audience: str = Field("account")
    issuer: str | None = Field(None)

    reload_public_key: bool = Field(True)
    public_key_reloading_minimum_age: datetime.timedelta = Field(datetime.timedelta(seconds=15))
    default_decoding_options: dict = Field(
        DEFAULT_OPTIONS,
        description="default options for jwt claims validation. These will be used"
        " if no options are provided explicitely on invoking the verify_token"
        " method of the BearerVerifier",
    )
    allowed_algorithms: list[str] = Field(
        default_factory=lambda: list(DEFAULT_ALLOWED_ALGORITHMS),
        description="Signature algorithms accepted when verifying bearer tokens."
        " Must contain only asymmetric algorithms (the verification key is a public"
        " key), otherwise algorithm-confusion attacks become possible.",
    )
    verify_ssl: bool = Field(True)


class BearerVerifier:
    """Bearer verifier class with key (re)loading

    joserfc does not fetch public keys for signature checking from an url itself.
    Since some auth backends update their public keys from time to time we
    implement automatic (re)loading of keys from url here.
    """

    def __init__(self, verifier_options: BearerVerifierOptions):
        self.verifier_options = verifier_options
        self._public_key_data: dict | None = None
        self._key_retrieved: datetime.datetime | None = None
        self._public_key_lock = threading.Lock()

    @classmethod
    def from_verifier_options(
        cls,
        auth_url: str,
        audience: str | None = "account",
        issuer: str | None = None,
        reload_public_key: bool = True,
        public_key_reloading_minimum_age: datetime.timedelta = datetime.timedelta(seconds=15),
        default_decoding_options: dict = DEFAULT_OPTIONS,
        allowed_algorithms: list[str] | None = None,
        verify_ssl: bool = True,
    ) -> BearerVerifier:
        """Return a 'BearerVerifier' object bases on the provided parameters."""
        return cls(
            BearerVerifierOptions(
                auth_url=auth_url,
                audience=audience,
                issuer=issuer,
                reload_public_key=reload_public_key,
                public_key_reloading_minimum_age=public_key_reloading_minimum_age,
                default_decoding_options=default_decoding_options,
                allowed_algorithms=(
                    allowed_algorithms
                    if allowed_algorithms is not None
                    else list(DEFAULT_ALLOWED_ALGORITHMS)
                ),
                verify_ssl=verify_ssl,
            )
        )

    def _key_set(self) -> KeySet:
        """Build a joserfc key set from the loaded public key data.

        The auth server may provide either a JWK set ({"keys": [...]}) or a
        single JWK. Raises ValueError / JoseError on unusable key data, which
        verify_token handles by trying to reload keys.
        """
        key_data = self._public_key_data
        if not isinstance(key_data, dict):
            raise ValueError("No usable public key data loaded from auth service.")
        if "keys" in key_data:
            return KeySet.import_key_set(cast(KeySetSerialization, key_data))
        return KeySet([JWKRegistry.import_key(key_data)])

    def _claims_registry(self, options: dict) -> jwt.JWTClaimsRegistry:
        """Translate decoding options into a joserfc claims registry.

        If an expected audience / issuer is configured, the respective claim is
        required ("essential") in the token and validated against the configured
        value — tokens lacking the claim are rejected. exp and nbf timestamps are
        validated whenever present.
        """
        claims_options: dict = {
            "exp": {"essential": options.get("require_exp", False)},
            "nbf": {"essential": False},
        }
        if options.get("verify_aud", True) and self.verifier_options.audience:
            claims_options["aud"] = {
                "essential": True,
                "value": self.verifier_options.audience,
            }
        if options.get("verify_iss", True) and self.verifier_options.issuer:
            claims_options["iss"] = {
                "essential": True,
                "value": self.verifier_options.issuer,
            }
        return jwt.JWTClaimsRegistry(**claims_options)

    async def verify_token(
        self,
        access_token: str,
        options: dict | None = None,
        force_loading_keys: bool = False,
    ) -> dict:
        """Try to verifiy the given acces token.

        Return the decoded bearer token or raise an AuthentificationError.
        """

        await self._obtain_public_key_data(force=force_loading_keys)

        if options is None:
            options = self.verifier_options.default_decoding_options
        try:
            token = jwt.decode(
                access_token,
                key=self._key_set(),
                algorithms=self.verifier_options.allowed_algorithms,
            )
            self._claims_registry(options).validate(token.claims)
        except (JoseError, ValueError) as e:
            logger.info("Failing to verify Bearer Token:\nError: %s", str(e))
            if not force_loading_keys:
                logger.info("Trying to load current public key")
                if self.verifier_options.reload_public_key and self.is_key_old():
                    # try again but force reloading key
                    return await self.verify_token(
                        access_token=access_token,
                        options=options,
                        force_loading_keys=True,
                    )
            raise AuthentificationError("Failed to verify Bearer Token") from e
        decoded_bearer_token: dict = token.claims
        return decoded_bearer_token

    def is_key_old(self) -> bool:
        """Check if the key is older than public_key_reloading_minimum_age.

        Also returns true if the _key_retrieved is None.
        """
        if self._key_retrieved is None:
            return True

        return (
            datetime.datetime.now(datetime.UTC) - self._key_retrieved  # noqa: DTZ003
        ) > self.verifier_options.public_key_reloading_minimum_age

    async def _obtain_public_key_data(self, force: bool = False) -> None:
        if self._public_key_data is not None and not force:
            # do not reload key if not forced
            return
        url = self.verifier_options.auth_url
        logger.info("Getting public key from auth service...")
        try:
            async with httpx.AsyncClient(
                verify=self.verifier_options.verify_ssl, timeout=15
            ) as client:
                resp = await client.get(url)
        except httpx.HTTPError as e:
            logger.info(
                "Error trying to get public key from auth service.Request failed: %s",
                str(e),
            )
            raise AuthentificationError(
                "Error trying to get public key from auth service. Request failed."
            ) from None

        try:
            key_data = resp.json()
        except json.JSONDecodeError as e:
            logger.info(
                "Error trying to get public key from auth service. Failed to decode json: %s",
                str(e),
            )
            raise AuthentificationError(
                "Error trying to get public key from auth service. Failed to decode json."
            ) from None

        with self._public_key_lock:
            self._public_key_data = key_data
            self._key_retrieved = datetime.datetime.now(datetime.UTC)  # noqa: DTZ003
