import json
import logging
import os
from copy import deepcopy
from datetime import datetime, timedelta
from posixpath import join as posix_urljoin
from unittest import mock
from uuid import UUID, uuid4

from hetdesrun.exportimport.importing import (
    deprecate_all_but_latest_in_group,
    import_transformation,
    import_transformations,
    load_json,
    transformation_revision_from_python_code,
)
from hetdesrun.persistence import sessionmaker
from hetdesrun.persistence.dbservice.revision import read_single_transformation_revision
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.webservice.config import get_config


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
            "hetdesrun.exportimport.importing.deprecate_all_but_latest_in_group",
            return_value=None,
        ) as patched_deprecate_group:

            import_transformations(
                "./transformations/components", deprecate_older_revisions=True
            )

    assert patched_deprecate_group.call_count > 10


def test_deprecate_all_but_latest_in_group():
    path = os.path.join(
        "tests",
        "data",
        "components",
        "alerts-from-score_100_38f168ef-cb06-d89c-79b3-0cd823f32e9d.json",
    )
    with open(path) as f:
        import_wf_json = json.load(f)
    stored_wf_json = deepcopy(import_wf_json)
    stored_wf_json["id"] = str(uuid4())
    stored_wf_json["version_tag"] = "0.1.0"
    stored_wf_json["released_timestamp"] = datetime.isoformat(
        datetime.fromisoformat(import_wf_json["released_timestamp"])
        - timedelta(weeks=1)
    )
    stored_wf = TransformationRevision(**stored_wf_json)
    stored_wf.deprecate()
    deprecated_stored_json = json.loads(stored_wf.json())

    get_response_mock = mock.Mock()
    get_response_mock.status_code = 200
    get_response_mock.json = mock.Mock(return_value=[import_wf_json, stored_wf_json])
    with mock.patch(
        "hetdesrun.exportimport.importing.requests.get", return_value=get_response_mock
    ) as patched_get:
        put_response_mock = mock.Mock()
        put_response_mock.status_code = 201
        with mock.patch(
            "hetdesrun.exportimport.importing.requests.put",
            return_value=put_response_mock,
        ) as patched_put:
            deprecate_all_but_latest_in_group(revision_group_id=import_wf_json["revision_group_id"])

            assert patched_get.call_count == 1

            assert patched_put.call_count == 1
            _, args, kwargs = patched_put.mock_calls[0]
            assert args[0] == posix_urljoin(
                get_config().hd_backend_api_url,
                "transformations",
                stored_wf_json["id"],
            )
            assert "json" in kwargs
            put_request_json = kwargs["json"]
            del put_request_json["disabled_timestamp"]
            del deprecated_stored_json["disabled_timestamp"]
            assert put_request_json == deprecated_stored_json
