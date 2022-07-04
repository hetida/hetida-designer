import logging
from unittest import mock

import pytest

from hetdesrun.exportimport.importing import import_transformations
from hetdesrun.persistence import get_db_engine, sessionmaker
from hetdesrun.persistence.dbmodels import Base


@pytest.fixture(scope="function")
def clean_test_db_engine(use_in_memory_db):
    if use_in_memory_db:
        in_memory_database_url = "sqlite+pysqlite:///:memory:"
        engine = get_db_engine(override_db_url=in_memory_database_url)
    else:
        engine = get_db_engine()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    return engine


def test_component_deployment_via_rest_api(caplog):
    response_mock = mock.Mock()
    response_mock.status_code = 200

    with caplog.at_level(logging.DEBUG):

        with mock.patch(
            "hetdesrun.utils.requests.put", return_value=response_mock
        ) as patched_put:
            caplog.clear()
            import_transformations("./transformations/components")
            assert "Reduce data set by leaving out values" in caplog.text
            # name of a component

    # at least tries to upload many components (we have more than 10 there)
    assert patched_put.call_count > 10

    # Test logging when posting does not work
    response_mock.status_code = 400

    with caplog.at_level(logging.INFO):
        with mock.patch(
            "hetdesrun.utils.requests.put", return_value=response_mock
        ) as patched_put:
            caplog.clear()
            import_transformations("./transformations/components")
            assert "COULD NOT PUT COMPONENT" in caplog.text


def test_workflow_deployment_via_rest_api(caplog):
    response_mock = mock.Mock()
    response_mock.status_code = 200

    with mock.patch(
        "hetdesrun.utils.requests.put", return_value=response_mock
    ) as patched_put:
        import_transformations("./transformations/workflows")

    # at least tries to upload many workflows
    assert patched_put.call_count > 3
    # Test logging when posting does not work
    response_mock.status_code = 400
    with mock.patch(
        "hetdesrun.utils.requests.put", return_value=response_mock
    ) as patched_put:
        caplog.clear()
        import_transformations("./transformations/workflows")
        assert "COULD NOT PUT WORKFLOW" in caplog.text


def test_component_deployment_directly_into_db(caplog, clean_test_db_engine):
    patched_session = sessionmaker(clean_test_db_engine)
    with mock.patch(
        "hetdesrun.persistence.dbservice.nesting.Session",
        patched_session,
    ):
        with mock.patch(
            "hetdesrun.persistence.dbservice.revision.Session",
            patched_session,
        ):
            response_mock = mock.Mock()
            response_mock.status_code = 200

            with caplog.at_level(logging.DEBUG):

                with mock.patch(
                    "hetdesrun.utils.requests.put", return_value=response_mock
                ) as patched_put:
                    caplog.clear()
                    import_transformations(
                        "./transformations/components", directly_into_db=True
                    )
                    assert "1946d5f8-44a8-724c-176f-16f3e49963af" in caplog.text
                    # id of a component

            # did not try to upload via REST API
            assert patched_put.call_count == 0
