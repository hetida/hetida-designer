import datetime
import json
import logging
import threading

import httpx
from jose import JOSEError, jwt
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AuthentificationError(Exception):
    pass


DEFAULT_OPTIONS = {
    "verify_signature": True,
    "verify_aud": False,
    "verify_iss": False,
    "require": ["exp"],
    # expiration will only be checked by jose if it is present,
    # so we require it
}


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

    reload_public_key: bool = Field(True)
    public_key_reloading_minimum_age: datetime.timedelta = Field(datetime.timedelta(seconds=15))
    default_decoding_options: dict = Field(
        DEFAULT_OPTIONS,
        description="default options for jwt decoding. These will be used"
        " if no options are provided explicitely on invoking the verify_token"
        " method of the BearerVerifier",
    )
    verify_ssl: bool = Field(True)


class BearerVerifier:
    """Bearer verifier class with key (re)loading

    * python-jose does not support loading public keys for signature check
      from an url at all at the moment.
    * PyJWT supports that but has insufficient error handling parsing key data
      and does not try to reload keys. Since some auth backends update their public
      keys from time to time we implement automatic reloading of keys from url here.
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
        audience: str = "account",
        reload_public_key: bool = True,
        public_key_reloading_minimum_age: datetime.timedelta = datetime.timedelta(seconds=15),
        default_decoding_options: dict = DEFAULT_OPTIONS,
        verify_ssl: bool = True,
    ) -> "BearerVerifier":
        """Return a 'BearerVerifier' object bases on the provided parameters."""
        return cls(
            BearerVerifierOptions(
                auth_url=auth_url,
                audience=audience,
                reload_public_key=reload_public_key,
                public_key_reloading_minimum_age=public_key_reloading_minimum_age,
                default_decoding_options=default_decoding_options,
                verify_ssl=verify_ssl,
            )
        )

    def verify_token(
        self,
        access_token: str,
        options: dict | None = None,
        force_loading_keys: bool = False,
    ) -> dict:
        """Try to verifiy the given acces token.

        Return the decoded bearer token or raise an AuthentificationError.
        """

        self._obtain_public_key_data(force=force_loading_keys)

        if options is None:
            options = self.verifier_options.default_decoding_options
        try:
            decoded_bearer_token: dict = jwt.decode(
                access_token,
                key=self._public_key_data,
                audience=self.verifier_options.audience,
                options=options,
            )
        except JOSEError as e:  # this is the base exception class of jose
            logger.info("Failing to verify Bearer Token: %s\nError: %s", access_token, str(e))
            if not force_loading_keys:
                logger.info("Trying to load current public key")
                if self.verifier_options.reload_public_key and self.is_key_old():
                    # try again but force reloading key
                    return self.verify_token(
                        access_token=access_token,
                        options=options,
                        force_loading_keys=True,
                    )
            raise AuthentificationError("Failed to verify Bearer Token") from e
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

    def _obtain_public_key_data(self, force: bool = False) -> None:
        if self._public_key_data is not None and not force:
            # do not reload key if not forced
            return
        url = self.verifier_options.auth_url
        try:
            resp = httpx.get(url, verify=self.verifier_options.verify_ssl, timeout=15)
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
