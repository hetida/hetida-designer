import logging
from unittest import mock

import pytest

from hetdesrun.webservice.config import RoleToRuntimeEngineUrlMapping, get_config
from hetdesrun.webservice.runtime_engine_url import get_runtime_engine_url


def test_engine_url_logic_without_auth():
    # default configuration works
    assert get_runtime_engine_url() == get_config().hd_runtime_engine_url

    with mock.patch(
        "hetdesrun.webservice.config.runtime_config.hd_runtime_engine_url",
        "test_default_engine_url",
    ):
        assert get_runtime_engine_url() == "test_default_engine_url"

        with mock.patch(
            "hetdesrun.webservice.config.runtime_config.is_runtime_service",
            False,
        ):
            assert get_runtime_engine_url() == "test_default_engine_url"


@pytest.mark.usefixtures("_valid_access_token_with_several_roles_in_context")
def test_engine_url_logic_with_auth(activate_auth, caplog):
    with mock.patch(
        "hetdesrun.webservice.config.runtime_config.hd_runtime_engine_url",
        "test_default_engine_url",
    ):
        assert get_runtime_engine_url() == "test_default_engine_url"

        with mock.patch(
            "hetdesrun.webservice.config.runtime_config.auth_role_key",
            "some_roles",
        ):
            with mock.patch(
                "hetdesrun.webservice.config.runtime_config.auth_runtime_engine_url_by_role",
                RoleToRuntimeEngineUrlMapping(
                    {"privileged_hd_user": "test_privileged_runtime_url"}
                ),
            ):
                assert get_runtime_engine_url() == "test_privileged_runtime_url"
            with mock.patch(  # noqa: SIM117
                "hetdesrun.webservice.config.runtime_config.auth_runtime_engine_url_by_role",
                RoleToRuntimeEngineUrlMapping(
                    {"a_role_not_in_the_token_payload": "test_privileged_runtime_url"}
                ),
            ):
                # should fallback
                with caplog.at_level(logging.WARN):
                    assert get_runtime_engine_url() == "test_default_engine_url"
                # we get a warning log message:
                assert "could not find a role" in caplog.text
