from unittest import mock

import pytest
from fastapi import HTTPException
from pydantic import SecretStr

from hetdesrun.backend.service.maintenance_router import (
    delete_all_and_refill,
    delete_unused_deprecated,
    handle_maintenance_operation_request,
)
from hetdesrun.exportimport.importing import import_transformations_from_dir
from hetdesrun.exportimport.utils import get_transformation_revisions


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
            "purge",
            SecretStr("wrong_secret"),
            delete_all_and_refill,
            mock.Mock,
            directly_in_db=True,
        )
    assert exc_info.value.status_code == 403


def test_maintenance_working(maintenance_secret_set, mocked_clean_test_db_session):
    maint_response = handle_maintenance_operation_request(
        "purge",
        SecretStr("testsecret"),
        delete_all_and_refill,
        mock.Mock,
        directly_in_db=True,
    )
    assert maint_response.success
    assert maint_response.error is None


def test_maintenance_with_kwargs(maintenance_secret_set, mocked_clean_test_db_session):

    import_transformations_from_dir("./tests/data/import_dir_components", directly_into_db=True)

    maint_response = handle_maintenance_operation_request(
        maintenance_operation_name="purge",
        secret_str=SecretStr("testsecret"),
        func=delete_unused_deprecated,
        response=mock.Mock,
        directly_in_db=True,
        exclude=["1946d5f8-44a8-724c-176f-123456aaaa22"],
        cutoff_date="2026-01-01 00:00:00Z",
    )

    # check that function works successfully
    assert maint_response.success
    assert maint_response.error is None

    # check if disabled components are deleted as expected
    tr_list_after = get_transformation_revisions(
        directly_from_db=True,
    )
    names = [i.name for i in tr_list_after]
    assert "Pass Through NEW" in names
    assert "Pass Through OLD" not in names
    assert "Pass Through EXCLUDE" in names


def test_maintenance_arbitrary_error(maintenance_secret_set):
    def raising_func(**kwargs):
        raise Exception("Something went wrong.")

    resp_mock = mock.Mock
    maint_response = handle_maintenance_operation_request(
        "purge", SecretStr("testsecret"), raising_func, resp_mock, directly_in_db=True
    )
    assert not maint_response.success
    assert maint_response.error is not None
    assert resp_mock.status_code == 500
