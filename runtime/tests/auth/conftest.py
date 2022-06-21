import datetime
from typing import List, Optional, Union
from unittest import mock
from uuid import uuid4

import pytest
import pytest_asyncio
from cryptography.hazmat.backends import default_backend as crypto_default_backend
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import AsyncClient
from jose import constants, jwk, jwt

from hetdesrun.persistence import sessionmaker
from hetdesrun.webservice.application import init_app


@pytest.fixture(scope="package")
def activate_auth():
    with mock.patch(
        "hetdesrun.webservice.config.runtime_config.auth", True
    ) as _fixture:
        yield _fixture


@pytest.fixture(scope="package")
def app_with_auth(activate_auth):
    yield init_app()


@pytest.fixture
def async_test_client_with_auth(app_with_auth):
    return AsyncClient(app=app_with_auth, base_url="http://test")


@pytest_asyncio.fixture
async def open_async_test_client_with_auth(async_test_client_with_auth):
    async with async_test_client_with_auth as ac:
        yield ac


@pytest.fixture(scope="session")
def key_pair():
    """RS256 key pair for auth testing purposes"""
    return gen_jose_rs256_key_pair()


@pytest.fixture(scope="session")
def wrong_key_pair():
    """RS256 key pair for auth testing purposes"""
    # hopefully different
    return gen_jose_rs256_key_pair()


@pytest.fixture(scope="function")
def valid_access_token(key_pair):
    return generate_token(algorithm="RS256", key=key_pair[0])


@pytest.fixture(scope="function")
def second_valid_access_token(key_pair):
    return generate_token(payload={"sub": "second"}, algorithm="RS256", key=key_pair[0])


@pytest.fixture(scope="function")
def wrong_key_access_token(wrong_key_pair):
    return generate_token(algorithm="RS256", key=wrong_key_pair[0])


@pytest.fixture(scope="function")
def mocked_clean_test_db_session(clean_test_db_engine):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ) as _fixture:
        yield _fixture


@pytest.fixture(scope="session")
def mocked_pre_loaded_public_key(key_pair):
    with mock.patch(
        "hetdesrun.webservice.auth_dependency.bearer_verifier._public_key_data",
        key_pair[1],
    ) as _fixture:
        yield _fixture


@pytest.fixture(scope="session")
def mocked_pre_loaded_wrong_public_key(wrong_key_pair):
    with mock.patch(
        "hetdesrun.webservice.auth_dependency.bearer_verifier._public_key_data",
        wrong_key_pair[1],
    ) as _fixture:
        yield _fixture


@pytest.fixture(scope="function")
def mocked_public_key_fetching(key_pair):
    def _mocked_obtain_public_key(self, force: bool = False):
        if self._public_key_data is not None and not force:
            # do not reload key if not forced
            return
        self._public_key_data = key_pair[1]
        _mocked_obtain_public_key.called = _mocked_obtain_public_key.called + 1

    _mocked_obtain_public_key.called = 0

    with mock.patch(
        "hetdesrun.webservice.auth_dependency.BearerVerifier._obtain_public_key_data",
        _mocked_obtain_public_key,
    ) as _fixture:
        yield _fixture


def datetime_to_unix_seconds(dt):
    return int(dt.timestamp())


def generate_token(
    payload=None,
    exp_dt: Optional[datetime.datetime] = None,
    algorithm="HS256",
    key="secret",
    audience: Optional[Union[str, List[str]]] = None,
    expired_by_default=False,
):
    """Generate jwt tokens combining some defaults with a (partly) payload.

    Useful for easy access token generation in order to test auth.

    By default token will last 300s from now and partly provided payload
    will be filled with example values.

    Setting expired_by_default to True makes the token expired by default (i.e.
    if not overwritten with explicit exp_dt or "exp" value in payload.)

    Algorithm is by default symmetric HS256 (use same key to decode). If for
    example you want to use RS256, pass "RS256" to the algorithm keyword parameter
    and provide the private key to the key parameter.

    Usage:

    >>> generate_token() # doctest: +ELLIPSIS
    '...'

    """
    generated_payload = {
        "iss": "Example Issuer",  # issuer
        "sub": "test_case",  # subject: for whom is the claim
        "iat": str(datetime_to_unix_seconds(datetime.datetime.now())),  # issued at
        "nbf": str(
            datetime_to_unix_seconds(datetime.datetime.now()) - 30
        ),  # not before
        # "aud": ["account"], # audience (target domain)
        "jti": str(uuid4()),  # jwt ID (token identifier making replication improssible)
        "exp": str(datetime_to_unix_seconds(exp_dt))
        if exp_dt is not None
        else (
            str(
                datetime_to_unix_seconds(
                    datetime.datetime.now() + datetime.timedelta(seconds=300)
                )
                - 600 * expired_by_default
            )
        ),
    }

    if audience is not None:
        generated_payload["audience"] = audience

    if payload is not None:
        generated_payload.update(payload)
    return jwt.encode(generated_payload, key, algorithm)


def verify_and_decode_token(token, key, audience=None, **kwargs):
    """Verifies and decodes token

    Returns the payload (sometimes called 'claim').

    Verifies signature and expiration (i.e. fails if signature is invalid
    or token is expired)

    Additional verifications (issuer, ...) can be given as keyword arguments.

    Usage:
        >>> t = generate_token(key="test")
        >>> verify_and_decode_token(t, key="test")  # doctest: +ELLIPSIS
        {...}

        Using wrong key makes verification fail:

        >>> verify_and_decode_token(t, key="wrong_key")  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        jose.exceptions.JWTError: Signature verification failed.

        Verification can be made to fail if expected claims are differing:

        >>> verify_and_decode_token(t, key="test", issuer="Other")  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        jose.exceptions.JWTClaimsError: Invalid issuer


        All Verification failures can be captured with jwt.JWTError

        >>> try:
        ...     verify_and_decode_token(t, key="test", issuer="Other")
        ... except JWTError:
        ...     print("Some JWT error occured")
        Some JWT error occured


    See gen_jose_rs256_key_pair function docstring for an
    asymmetric / RS256 usage example.

    """
    return jwt.decode(token=token, key=key, audience=audience, **kwargs)


# RS256 (asymmetric) example
# https://stackoverflow.com/a/39126754


def gen_jose_rs256_key_pair():
    """Generate RS256 asymmetric key pair for usage with python-jose

    Returns a tuple (private_key, public_key_jwk_dict) which can be used
    to sign (private_key) and verify (public_key_jwk_dict) tokens.

    Example usage:

        >>> private_key, public_key_jwk_dict = gen_jose_rs256_key_pair()

        >>> t = generate_token(key=private_key, algorithm="RS256")
        >>> claims = verify_and_decode_token(t, key=public_key_jwk_dict)
        >>> claims     # doctest: +ELLIPSIS
        {...}
    """

    key = rsa.generate_private_key(
        backend=crypto_default_backend(), public_exponent=65537, key_size=4096
    )

    private_key = key.private_bytes(
        encoding=crypto_serialization.Encoding.PEM,
        format=crypto_serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=crypto_serialization.NoEncryption(),
    )

    public_key_string = (
        key.public_key()
        .public_bytes(
            crypto_serialization.Encoding.PEM,
            crypto_serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("utf8")
    )

    public_key_jwk_dict = jwk.RSAKey(
        algorithm=constants.Algorithms.RS256, key=public_key_string
    ).to_dict()

    return (private_key, public_key_jwk_dict)
