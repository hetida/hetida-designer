from unittest import mock

import pytest
from fastapi import HTTPException
from pydantic import SecretStr

from hetdesrun.backend.service.maintenance_router import (
    delete_all_and_refill,
    handle_maintenance_operation_request,
)
from hetdesrun.persistence import sessionmaker


@pytest.fixture()
def maintenance_secret_set():
    with mock.patch(
        "hetdesrun.webservice.config.runtime_config.maintenance_secret",
        SecretStr("testsecret"),
    ) as _fixture:
        yield _fixture


def test_maintenance_incorrect_secret(maintenance_secret_set):
    with pytest.raises(HTTPException) as exc_info:
        handle_maintenance_operation_request(
            "purge", SecretStr("wrong_secret"), delete_all_and_refill, mock.Mock
        )
    assert exc_info.value.status_code == 403


def test_maintenance_working(maintenance_secret_set, clean_test_db_engine):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        maint_response = handle_maintenance_operation_request(
            "purge", SecretStr("testsecret"), delete_all_and_refill, mock.Mock
        )
    assert maint_response.success
    assert maint_response.error is None


def test_maintenance_arbitrary_error(maintenance_secret_set):
    def raising_func(**kwargs):
        raise Exception("Something went wrong.")

    resp_mock = mock.Mock
    maint_response = handle_maintenance_operation_request(
        "purge", SecretStr("testsecret"), raising_func, resp_mock
    )
    assert not maint_response.success
    assert maint_response.error is not None
    assert resp_mock.status_code == 500
