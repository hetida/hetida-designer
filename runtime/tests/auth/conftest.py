import datetime
from copy import deepcopy
from unittest import mock
from uuid import uuid4

import pytest
import pytest_asyncio
from cryptography.hazmat.backends import default_backend as crypto_default_backend
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient
from joserfc import jwt
from joserfc.jwk import OctKey, RSAKey
from pydantic import SecretStr

from hetdesrun.webservice.application import init_app
from hetdesrun.webservice.auth_dependency import (
    ExternalAuthMode,
    InternalAuthMode,
)
from hetdesrun.webservice.auth_dependency import (
    set_request_auth_context as set_request_auth_context_func,
)
from hetdesrun.webservice.auth_outgoing import (
    ClientCredentialsGrantCredentials,
    ServiceCredentials,
)

token_response_stub = {
    "access_token": "nothing",
    "expires_in": 1200,
    "refresh_expires_in": 1800,
    "refresh_token": "nothing",
    "token_type": "bearer",
    "not-before-policy": 0,
    "scope": "email profile",
    "session_state": "123",
}


@pytest.fixture()
def valid_token_response(valid_access_token):
    token_response_dict = deepcopy(token_response_stub)
    token_response_dict["access_token"] = valid_access_token
    token_response_dict["refresh_token"] = valid_access_token

    return token_response_dict


@pytest.fixture()
def mocked_token_request(valid_token_response):
    mocked_resp = mock.Mock
    mocked_resp.json = mock.Mock(return_value=valid_token_response)

    async def mocked_post_to_auth_provider(*args, **kwargs):
        mocked_post_to_auth_provider.last_called_args = deepcopy(args)
        mocked_post_to_auth_provider.last_called_kwargs = deepcopy(kwargs)
        return mocked_resp

    mocked_post_to_auth_provider.token_response_dict = deepcopy(valid_token_response)

    with mock.patch(
        "hetdesrun.webservice.auth_outgoing.post_to_auth_provider",
        mocked_post_to_auth_provider,
    ) as test_mocked_post_to_auth_provider:
        yield test_mocked_post_to_auth_provider


@pytest.fixture()
def outgoing_auth_internal_mode_off():
    with mock.patch(
        "hetdesrun.webservice.config.runtime_config.internal_auth_mode",
        InternalAuthMode.OFF,
    ) as _fixture:
        yield _fixture


@pytest.fixture()
def outgoing_auth_external_mode_off():
    with mock.patch(
        "hetdesrun.webservice.config.runtime_config.external_auth_mode",
        ExternalAuthMode.OFF,
    ) as _fixture:
        yield _fixture


@pytest.fixture()
def outgoing_auth_internal_mode_forward_or_fixed():
    with mock.patch(
        "hetdesrun.webservice.config.runtime_config.internal_auth_mode",
        InternalAuthMode.FORWARD_OR_FIXED,
    ) as _fixture:
        yield _fixture


@pytest.fixture()
def outgoing_auth_external_mode_forward_or_fixed():
    with mock.patch(
        "hetdesrun.webservice.config.runtime_config.external_auth_mode",
        ExternalAuthMode.FORWARD_OR_FIXED,
    ) as _fixture:
        yield _fixture


@pytest.fixture()
def outgoing_auth_internal_mode_client():
    with mock.patch(
        "hetdesrun.webservice.config.runtime_config.internal_auth_mode",
        InternalAuthMode.CLIENT,
    ) as _fixture:
        yield _fixture


@pytest.fixture()
def outgoing_auth_external_mode_client():
    with mock.patch(
        "hetdesrun.webservice.config.runtime_config.external_auth_mode",
        ExternalAuthMode.CLIENT,
    ) as _fixture:
        yield _fixture


@pytest.fixture()
def auth_bearer_token_for_outgoing_requests_is_set():
    with mock.patch(
        "hetdesrun.webservice.config.runtime_config.auth_bearer_token_for_outgoing_requests",
        SecretStr("some token string"),
    ) as _fixture:
        yield _fixture


@pytest.fixture()
def auth_bearer_token_for_outgoing_requests_not_set():
    with mock.patch(
        "hetdesrun.webservice.config.runtime_config.auth_bearer_token_for_outgoing_requests",
        None,
    ) as _fixture:
        yield _fixture


@pytest.fixture()
def set_request_auth_context():
    with mock.patch(
        "hetdesrun.webservice.auth_dependency.get_request_auth_context",
        return_value={"token": "token from request"},
    ) as _fixture:
        yield _fixture


@pytest.fixture()
def unset_request_auth_context():
    with mock.patch(
        "hetdesrun.webservice.auth_dependency.get_request_auth_context",
        return_value={},
    ) as _fixture:
        yield _fixture


@pytest.fixture(scope="package")
def service_client_credentials():
    return ServiceCredentials(
        realm="my-realm",
        grant_credentials=ClientCredentialsGrantCredentials(
            client_id="my-client",
            client_secret="my-client-secret",  # noqa: S106
        ),
        auth_url="https://test.com/auth",
        post_client_kwargs={"verify": False},
    )


@pytest.fixture()
def set_external_client_creds(service_client_credentials):
    with mock.patch(
        "hetdesrun.webservice.config.runtime_config.external_auth_client_credentials",
        service_client_credentials,
    ) as _fixture:
        yield _fixture


@pytest.fixture()
def set_internal_client_creds(service_client_credentials):
    with mock.patch(
        "hetdesrun.webservice.config.runtime_config.internal_auth_client_credentials",
        service_client_credentials,
    ) as _fixture:
        yield _fixture


@pytest.fixture(scope="package")
def activate_auth():
    with mock.patch("hetdesrun.webservice.config.runtime_config.auth", True) as _fixture:
        yield _fixture


@pytest.fixture(scope="package")
def app_with_auth(activate_auth):
    return init_app()


@pytest.fixture
def async_test_client_with_auth(app_with_auth):
    return AsyncClient(transport=ASGITransport(app=app_with_auth), base_url="http://test")


@pytest_asyncio.fixture
async def open_async_test_client_with_auth(async_test_client_with_auth):
    async with async_test_client_with_auth as ac:
        yield ac


@pytest.fixture(scope="session")
def key_pair():
    """RS256 key pair for auth testing purposes"""
    return gen_rs256_key_pair()


@pytest.fixture(scope="session")
def wrong_key_pair():
    """RS256 key pair for auth testing purposes"""
    # hopefully different
    return gen_rs256_key_pair()


@pytest.fixture()
def valid_access_token(key_pair):
    return generate_token(algorithm="RS256", key=key_pair[0])


@pytest.fixture()
def valid_access_token_with_role(key_pair):
    return generate_token(
        algorithm="RS256", key=key_pair[0], payload={"some_roles": ["allowed_hd_user"]}
    )


@pytest.fixture()
def access_token_without_exp(key_pair):
    # a validly signed token that lacks the exp claim
    return jwt.encode(
        {"alg": "RS256"},
        {
            "iss": "Example Issuer",
            "sub": "test_case",
            "aud": ["account"],
            "jti": str(uuid4()),
        },
        RSAKey.import_key(key_pair[0]),
    )


@pytest.fixture()
def access_token_without_aud(key_pair):
    # a validly signed, unexpired token that lacks the aud claim
    return jwt.encode(
        {"alg": "RS256"},
        {
            "iss": "Example Issuer",
            "sub": "test_case",
            "jti": str(uuid4()),
            "exp": datetime_to_unix_seconds(
                datetime.datetime.now() + datetime.timedelta(seconds=300)  # noqa: DTZ005
            ),
        },
        RSAKey.import_key(key_pair[0]),
    )


@pytest.fixture()
def access_token_with_wrong_aud(key_pair):
    return generate_token(
        algorithm="RS256", key=key_pair[0], payload={"aud": ["some-other-audience"]}
    )


@pytest.fixture()
def valid_access_token_with_string_role(key_pair):
    # role claim is a single string (not a list) that contains the allowed role
    # "allowed_hd_user" as a substring
    return generate_token(
        algorithm="RS256", key=key_pair[0], payload={"some_roles": "superallowed_hd_user_x"}
    )


@pytest.fixture()
def valid_access_token_with_several_roles(key_pair):
    return generate_token(
        algorithm="RS256",
        key=key_pair[0],
        payload={
            "some_roles": [
                "some_other_role",
                "allowed_hd_user",
                "privileged_hd_user",
                "some_other_role",
            ]
        },
    )


@pytest.fixture()
def _valid_access_token_with_several_roles_in_context(key_pair):
    payload = {
        "some_roles": [
            "some_other_role",
            "allowed_hd_user",
            "privileged_hd_user",
            "some_other_role",
        ]
    }
    token = generate_token(
        algorithm="RS256",
        key=key_pair[0],
        payload=payload,
    )
    set_request_auth_context_func({"token": token, "payload": payload})
    yield
    set_request_auth_context_func({})


@pytest.fixture()
def second_valid_access_token(key_pair):
    return generate_token(payload={"sub": "second"}, algorithm="RS256", key=key_pair[0])


@pytest.fixture()
def wrong_key_access_token(wrong_key_pair):
    return generate_token(algorithm="RS256", key=wrong_key_pair[0])


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


@pytest.fixture()
def mocked_public_key_fetching(key_pair):
    async def _mocked_obtain_public_key(self, force: bool = False):
        if self._public_key_data is not None and not force:
            # do not reload key if not forced
            _mocked_obtain_public_key.called = _mocked_obtain_public_key.called + 1
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


def as_joserfc_key(key, algorithm):
    """Wrap raw key material into a joserfc key object.

    Accepts plain secret strings for symmetric HS* algorithms and
    PEM strings/bytes for asymmetric RS* algorithms.
    """
    if algorithm.startswith("HS"):
        return OctKey.import_key(key)
    if algorithm.startswith("RS"):
        return RSAKey.import_key(key)
    raise ValueError(f"Cannot wrap key material for algorithm {algorithm}")


def generate_token(
    payload=None,
    exp_dt: datetime.datetime | None = None,
    algorithm="HS256",
    key="secret",
    audience: str | list[str] | None = None,
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
    and provide the private key (PEM) to the key parameter.
    """
    generated_payload = {
        "iss": "Example Issuer",  # issuer
        "sub": "test_case",  # subject: for whom is the claim
        "iat": datetime_to_unix_seconds(datetime.datetime.now()),  # noqa: DTZ005 # issued at
        "nbf": datetime_to_unix_seconds(datetime.datetime.now()) - 30,  # noqa: DTZ005 # not before
        "aud": ["account"],  # audience (target domain)
        "jti": str(uuid4()),  # jwt ID (token identifier making replication improssible)
        "exp": datetime_to_unix_seconds(exp_dt)
        if exp_dt is not None
        else (
            datetime_to_unix_seconds(
                datetime.datetime.now()  # noqa: DTZ005
                + datetime.timedelta(seconds=300)
            )
            - 600 * expired_by_default
        ),
    }

    if audience is not None:
        generated_payload["aud"] = audience

    if payload is not None:
        generated_payload.update(payload)
    return jwt.encode({"alg": algorithm}, generated_payload, as_joserfc_key(key, algorithm))


def gen_rs256_key_pair():
    """Generate RS256 asymmetric key pair for auth testing

    Returns a tuple (private_key, public_key_jwk_dict): the private key (PEM bytes)
    can be passed to generate_token to sign tokens, the public key JWK dict mimics
    the key data a BearerVerifier loads from the auth provider to verify them.
    """

    key = rsa.generate_private_key(
        # reduced keysize from 4096 for increasing test speed
        backend=crypto_default_backend(),
        public_exponent=65537,
        key_size=1024,  # noqa: S505
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

    public_key_jwk_dict = RSAKey.import_key(public_key_string, parameters={"alg": "RS256"}).as_dict(
        private=False
    )

    return (private_key, public_key_jwk_dict)
