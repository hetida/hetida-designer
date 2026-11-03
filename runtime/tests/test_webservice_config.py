import logging
from unittest import mock

import pytest
from pydantic import ValidationError

from hetdesrun.webservice.config import (
    RuntimeConfig,
    warn_if_database_settings_ignored,
    warn_if_environment_file_missing,
)


@pytest.mark.parametrize("environment_file", [None, ""])
def test_no_warning_without_environment_file(caplog, environment_file):
    with (
        mock.patch("hetdesrun.webservice.config.environment_file", environment_file),
        caplog.at_level(logging.WARNING),
    ):
        warn_if_environment_file_missing()

    assert "HD_RUNTIME_ENVIRONMENT_FILE" not in caplog.text


def test_no_warning_for_existing_environment_file(caplog, tmp_path):
    env_file = tmp_path / "existing.env"
    env_file.write_text('HD_DATABASE_URL="sqlite+pysqlite:///:memory:"\n')

    with (
        mock.patch("hetdesrun.webservice.config.environment_file", str(env_file)),
        caplog.at_level(logging.WARNING),
    ):
        warn_if_environment_file_missing()

    assert "HD_RUNTIME_ENVIRONMENT_FILE" not in caplog.text


@pytest.mark.parametrize("missing", ["missing.env", "a_directory"])
def test_warning_for_missing_environment_file(caplog, tmp_path, missing):
    (tmp_path / "a_directory").mkdir()
    env_file = tmp_path / missing

    with (
        mock.patch("hetdesrun.webservice.config.environment_file", str(env_file)),
        caplog.at_level(logging.WARNING),
    ):
        warn_if_environment_file_missing()

    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.WARNING
    assert "HD_RUNTIME_ENVIRONMENT_FILE was not found" in caplog.text
    assert str(env_file) in caplog.text


@pytest.mark.parametrize(
    ("env", "expected_port"),
    [
        ({}, 5432),
        ({"HD_DB_PORT": "5433"}, 5433),
        ({"HD_DATABASE_PORT": "5434"}, 5434),  # older name
        ({"HD_DB_PORT": "5433", "HD_DATABASE_PORT": "5434"}, 5433),
    ],
)
def test_db_port(monkeypatch, env, expected_port):
    for name in ("HD_DB_PORT", "HD_DATABASE_PORT", "HD_DATABASE_URL"):
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)

    config = RuntimeConfig(_env_file=None)  # type: ignore[call-arg]

    assert config.sqlalchemy_db_port == expected_port
    assert config.sqlalchemy_connection_string.port == expected_port


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("true", True),
        ("True", True),
        ("1", True),
        ("yes", True),
        ("on", True),
        ("t", True),
        ("false", False),
        ("0", False),
        ("no", False),
        ("off", False),
        ('"true"', None),  # e.g. from docker compose list syntax HD_...="true"
        ("true ", None),
        ("ok", None),
        ("", None),
    ],
)
def test_backend_start_flags(monkeypatch, value, expected):
    flags = {
        "HD_BACKEND_AUTODEPLOY_BASE_TRANSFORMATIONS": "autodeploy_base_transformations",
        "HD_BACKEND_PRESERVE_DB_ON_AUTODEPLOY": "preserve_db_on_autodeploy",
        "HD_BACKEND_ALLOW_OVERWRITE_RELEASED": "autodeploy_allow_overwrite_released",
        "HD_ALLOW_IN_MEMORY_DB": "allow_in_memory_db",
    }
    for env_name, field_name in flags.items():
        monkeypatch.setenv(env_name, value)
        if expected is None:
            with pytest.raises(ValidationError, match=env_name):
                RuntimeConfig(_env_file=None)  # type: ignore[call-arg]
        else:
            config = RuntimeConfig(_env_file=None)  # type: ignore[call-arg]
            assert getattr(config, field_name) is expected
        monkeypatch.delenv(env_name)


@pytest.mark.parametrize(
    ("env", "expected_ignored"),
    [
        ({}, None),
        ({"HD_DB_HOST": "dbhost"}, None),
        ({"HD_DATABASE_URL": "sqlite+pysqlite:///:memory:"}, None),
        (
            {"HD_DATABASE_URL": "sqlite+pysqlite:///:memory:", "HD_DB_HOST": "dbhost"},
            "HD_DB_HOST are ignored",
        ),
        (
            {
                "HD_DATABASE_URL": "sqlite+pysqlite:///:memory:",
                "HD_DATABASE_PORT": "5433",
                "HD_DB_PASSWORD": "secret",
            },
            "HD_DB_PORT (or HD_DATABASE_PORT), HD_DB_PASSWORD are ignored",
        ),
    ],
)
def test_warn_if_database_settings_ignored(monkeypatch, caplog, env, expected_ignored):
    for name in (
        "HD_DATABASE_URL",
        "HD_DB_HOST",
        "HD_DB_PORT",
        "HD_DATABASE_PORT",
        "HD_DB_PASSWORD",
    ):
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    config = RuntimeConfig(_env_file=None)  # type: ignore[call-arg]

    with (
        mock.patch("hetdesrun.webservice.config.get_config", return_value=config),
        caplog.at_level(logging.WARNING),
    ):
        warn_if_database_settings_ignored()

    if expected_ignored is None:
        assert "HD_DATABASE_URL is set" not in caplog.text
    else:
        assert len(caplog.records) == 1
        assert caplog.records[0].levelno == logging.WARNING
        assert expected_ignored in caplog.text
        assert "secret" not in caplog.text


def test_no_database_settings_warning_without_backend(monkeypatch, caplog):
    monkeypatch.setenv("HD_DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("HD_DB_HOST", "dbhost")
    monkeypatch.setenv("HD_IS_BACKEND_SERVICE", "false")
    config = RuntimeConfig(_env_file=None)  # type: ignore[call-arg]

    with (
        mock.patch("hetdesrun.webservice.config.get_config", return_value=config),
        caplog.at_level(logging.WARNING),
    ):
        warn_if_database_settings_ignored()

    assert "HD_DATABASE_URL is set" not in caplog.text
