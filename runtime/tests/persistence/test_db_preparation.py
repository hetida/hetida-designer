import logging
from unittest import mock

import pytest

from hetdesrun.persistence.db_preparation import (
    exit_unless_in_memory_db_allowed,
    prepare_db,
    prepare_db_before_gunicorn,
    run_migrations,
)

MODULE = "hetdesrun.persistence.db_preparation"


def test_run_migrations_retries():
    with (
        mock.patch(
            f"{MODULE}.command.upgrade", side_effect=[ValueError("db not up"), None]
        ) as mocked_upgrade,
        mock.patch(f"{MODULE}.time.sleep") as mocked_sleep,
        mock.patch("hetdesrun.webservice.config.runtime_config.target_alembic_revision", "abc"),
    ):
        run_migrations(alembic_dir="./some_dir", retry_wait_seconds=3)

    assert mocked_upgrade.call_count == 2
    alembic_cfg, target_revision = mocked_upgrade.call_args.args
    assert alembic_cfg.get_main_option("script_location") == "./some_dir"
    assert target_revision == "abc"
    mocked_sleep.assert_called_once_with(3)


def test_run_migrations_fails_finally(caplog):
    with (
        mock.patch(
            f"{MODULE}.command.upgrade", side_effect=ValueError("db not up")
        ) as mocked_upgrade,
        mock.patch(f"{MODULE}.time.sleep") as mocked_sleep,
        mock.patch("hetdesrun.webservice.config.runtime_config.target_alembic_revision", ""),
        pytest.raises(ValueError, match="db not up"),
    ):
        run_migrations(max_attempts=3)

    assert mocked_upgrade.call_count == 3
    assert mocked_upgrade.call_args.args[1] == "head"
    assert mocked_sleep.call_count == 2
    assert "Db migrations finally failed after 3 attempts" in caplog.text


@pytest.mark.parametrize("prepopulate", [True, False])
def test_prepare_db(prepopulate):
    calls = mock.Mock()
    with (
        mock.patch(f"{MODULE}.run_migrations", calls.run_migrations),
        mock.patch(
            f"{MODULE}.autodeploy_base_transformations", calls.autodeploy_base_transformations
        ),
        mock.patch(f"{MODULE}.prepopulate_structure", calls.prepopulate_structure),
        mock.patch(f"{MODULE}.autoimport_at_backend_start", calls.autoimport_at_backend_start),
        mock.patch(
            "hetdesrun.adapters.virtual_structure_adapter.config.vst_adapter_config"
            ".prepopulate_virtual_structure_adapter_at_designer_startup",
            prepopulate,
        ),
    ):
        prepare_db()

    assert [call[0] for call in calls.mock_calls] == [
        "run_migrations",
        "autodeploy_base_transformations",
        *(["prepopulate_structure"] if prepopulate else []),
        "autoimport_at_backend_start",
    ]


@pytest.mark.parametrize(
    ("allowed", "web_concurrency", "require_allowance", "gunicorn_mode", "expected_error"),
    [
        (False, None, True, False, "HD_ALLOW_IN_MEMORY_DB=true"),
        (True, "2", True, False, "(it is 2)"),
        (True, None, True, True, "deprecated gunicorn mode"),
        (True, None, True, False, None),
        (True, "1", True, False, None),
        # e.g. local development
        (False, None, False, False, None),
        (False, "2", False, False, "(it is 2)"),
    ],
)
def test_exit_unless_in_memory_db_allowed(  # noqa: PLR0913
    monkeypatch, caplog, allowed, web_concurrency, require_allowance, gunicorn_mode, expected_error
):
    if web_concurrency is None:
        monkeypatch.delenv("WEB_CONCURRENCY", raising=False)
    else:
        monkeypatch.setenv("WEB_CONCURRENCY", web_concurrency)

    with (
        mock.patch("hetdesrun.webservice.config.runtime_config.allow_in_memory_db", allowed),
        caplog.at_level(logging.WARNING),
    ):
        if expected_error is None:
            exit_unless_in_memory_db_allowed(
                require_allowance=require_allowance, gunicorn_mode=gunicorn_mode
            )
            assert ("Using an in-memory database as allowed" in caplog.text) is require_allowance
        else:
            with pytest.raises(SystemExit) as exc_info:
                exit_unless_in_memory_db_allowed(
                    require_allowance=require_allowance, gunicorn_mode=gunicorn_mode
                )
            assert exc_info.value.code == 1
            assert caplog.records[-1].levelno == logging.ERROR
            assert expected_error in caplog.records[-1].getMessage()


@pytest.mark.parametrize(
    ("is_backend", "in_memory", "expect_prepared", "expect_exit"),
    [
        (False, False, False, False),
        (True, False, True, False),
        (True, True, False, True),
    ],
)
def test_prepare_db_before_gunicorn(is_backend, in_memory, expect_prepared, expect_exit):
    with (
        mock.patch("hetdesrun.webservice.config.runtime_config.allow_in_memory_db", True),
        mock.patch("hetdesrun.webservice.config.runtime_config.is_backend_service", is_backend),
        mock.patch(f"{MODULE}.is_in_memory_db", return_value=in_memory),
        mock.patch(f"{MODULE}.prepare_db") as mocked_prepare_db,
    ):
        if expect_exit:
            with pytest.raises(SystemExit):
                prepare_db_before_gunicorn()
        else:
            prepare_db_before_gunicorn()

    assert mocked_prepare_db.called is expect_prepared
