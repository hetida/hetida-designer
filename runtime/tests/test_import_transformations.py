import logging
import os
from unittest import mock
from uuid import UUID

from hetdesrun.exportimport.importing import (
    import_transformation,
    import_transformations,
    load_json,
    transformation_revision_from_python_code,
)
from hetdesrun.persistence import sessionmaker
from hetdesrun.persistence.dbservice.revision import read_single_transformation_revision
from hetdesrun.persistence.models.transformation import TransformationRevision


def test_tr_from_code_for_component_without_register_decorator():
    path = os.path.join(
        "tests",
        "data",
        "components",
        "alerts-from-score_100_38f168ef-cb06-d89c-79b3-0cd823f32e9d.py",
    )
    with open(path) as f:
        code = f.read()

    tr_json = transformation_revision_from_python_code(code, path)

    tr = TransformationRevision(**tr_json)

    assert tr.name == "Alerts from Score"
    assert tr.category == "Anomaly Detection"
    assert "anomalous situations" in tr.description
    assert tr.version_tag == "1.0.0"
    assert str(tr.id) == "38f168ef-cb06-d89c-79b3-0cd823f32e9d"
    assert str(tr.revision_group_id) == "38f168ef-cb06-d89c-79b3-0cd823f32e9d"
    assert len(tr.io_interface.inputs) == 2
    assert len(tr.io_interface.outputs) == 1
    assert tr.type == "COMPONENT"
    assert "COMPONENT_INFO" in tr.content


def test_import_single_transformation(clean_test_db_engine):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        path = (
            "./transformations/components/arithmetic/"
            "consecutive-differences_100_ce801dcb-8ce1-14ad-029d-a14796dcac92.json"
        )
        tr_json = load_json(path)
        import_transformation(tr_json, path, directly_into_db=True)
        persisted_tr = read_single_transformation_revision(UUID(tr_json["id"]))
        tr = TransformationRevision(**tr_json)

        assert persisted_tr == tr


def test_component_import_via_rest_api(caplog):
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


def test_workflow_import_via_rest_api(caplog):
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


def test_component_import_directly_into_db(caplog, clean_test_db_engine):
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


def test_import_with_deprecate_older_versions():
    response_mock = mock.Mock()
    response_mock.status_code = 201

    with mock.patch("hetdesrun.utils.requests.put", return_value=response_mock):

        with mock.patch(
            "hetdesrun.exportimport.importing.deprecate_older_revisions_in_group",
            return_value=None,
        ) as patched_deprecate_group:

            import_transformations(
                "./transformations/components", deprecate_older_revisions=True
            )

    assert patched_deprecate_group.call_count > 10
