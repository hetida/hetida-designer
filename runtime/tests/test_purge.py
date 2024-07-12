import json
import logging
import os
from copy import deepcopy
from datetime import datetime, timedelta
from posixpath import join as posix_urljoin
from unittest import mock
from uuid import uuid4

import pytest

from hetdesrun.exportimport.purge import (
    delete_all_and_refill,
    delete_drafts,
    delete_unused_deprecated,
    deprecate_all_but_latest_per_group,
)
from hetdesrun.exportimport.utils import (
    delete_transformation_revision,
    delete_transformation_revisions,
    deprecate_all_but_latest_in_group,
    get_transformation_revisions,
    update_or_create_transformation_revision,
)
from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.persistence.dbservice.exceptions import DBIntegrityError, DBNotFoundError
from hetdesrun.persistence.models.exceptions import ModifyForbidden
from hetdesrun.persistence.models.io import IOInterface
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.persistence.models.workflow import WorkflowContent
from hetdesrun.trafoutils.filter.params import FilterParams
from hetdesrun.utils import State, Type
from hetdesrun.webservice.config import get_config

example_tr_draft = TransformationRevision(
    type=Type.COMPONENT,
    state=State.DRAFT,
    category="category",
    name="name",
    version_tag="1.0.0",
    description="",
    id=uuid4(),
    revision_group_id=uuid4(),
    io_interface=IOInterface(),
    content="",
    documentation="",
    test_wiring=WorkflowWiring(),
)

example_tr_released = deepcopy(example_tr_draft)
example_tr_released.id = uuid4()
example_tr_released.revision_group_id = uuid4()
example_tr_released_old = deepcopy(example_tr_released)
example_tr_released_old.id = uuid4()

example_tr_deprecated = deepcopy(example_tr_released)
example_tr_deprecated.id = uuid4()
example_tr_deprecated.revision_group_id = uuid4()


def test_get_transformation_revisions(caplog):
    tr_list = [example_tr_draft]
    with mock.patch(
        "hetdesrun.exportimport.utils.get_multiple_transformation_revisions",
        return_value=tr_list,
    ) as mocked_get_from_db:
        resp_mock = mock.Mock()
        resp_mock.status_code = 200
        resp_mock.json = mock.Mock(return_value=[json.loads(tr.json()) for tr in tr_list])
        with mock.patch(
            "hetdesrun.exportimport.utils.requests.get", return_value=resp_mock
        ) as mocked_get_from_backend:
            returned_from_db_tr_list = get_transformation_revisions(
                params=FilterParams(include_dependencies=False), directly_from_db=True
            )
            assert returned_from_db_tr_list == tr_list
            assert mocked_get_from_db.call_count == 1
            assert mocked_get_from_backend.call_count == 0
            _, args, kwargs = mocked_get_from_db.mock_calls[0]
            assert len(args) == 1
            assert len(kwargs) == 0
            assert isinstance(args[0], FilterParams)
            assert args[0].include_dependencies is False  # default value
            assert args[0].include_deprecated is True  # default value
            assert args[0].unused is False  # default value

            params = FilterParams(
                type=Type.COMPONENT,
                state=State.DRAFT,
                categories=[""],
                revision_group_id=uuid4(),
                ids=[uuid4(), uuid4()],
                names=["ö(-.-)ö", ","],
                include_dependencies=False,
            )
            returned_from_backend_tr_list = get_transformation_revisions(params)
            assert returned_from_backend_tr_list == tr_list
            assert mocked_get_from_db.call_count == 1  # no second call
            assert mocked_get_from_backend.call_count == 1
            _, args, kwargs = mocked_get_from_backend.mock_calls[0]
            assert args[0] == posix_urljoin(get_config().hd_backend_api_url, "transformations")
            assert kwargs["params"]["type"] == params.type.value
            assert kwargs["params"]["state"] == params.state.value
            assert kwargs["params"]["category"] == params.categories
            assert kwargs["params"]["revision_group_id"] == str(params.revision_group_id)
            assert kwargs["params"]["id"] == [str(id_) for id_ in params.ids]
            assert kwargs["params"]["name"] == params.names
            assert kwargs["params"]["include_deprecated"] is True
            assert kwargs["params"]["unused"] is False

    with caplog.at_level(logging.ERROR):
        resp_mock = mock.Mock()
        resp_mock.status_code = 500
        with mock.patch(
            "hetdesrun.exportimport.utils.requests.get", return_value=resp_mock
        ) as mocked_get_from_backend:
            caplog.clear()
            returned_tr_list = get_transformation_revisions()
            assert returned_tr_list == []
            assert "COULD NOT GET transformation revisions." in caplog.text


def test_delete_transformation_revision(caplog):
    with mock.patch(
        "hetdesrun.exportimport.utils.delete_single_transformation_revision",
        return_value=None,
    ) as mocked_delete_from_db:
        resp_mock = mock.Mock()
        resp_mock.status_code = 204
        with mock.patch(
            "hetdesrun.exportimport.utils.requests.delete", return_value=resp_mock
        ) as mocked_delete_from_backend:
            id_ = uuid4()
            delete_transformation_revision(id_, directly_in_db=True)
            assert mocked_delete_from_db.call_count == 1
            assert mocked_delete_from_backend.call_count == 0
            _, args, kwargs = mocked_delete_from_db.mock_calls[0]
            assert args[0] == id_
            assert kwargs["ignore_state"] is True

            delete_transformation_revision(id_)
            assert mocked_delete_from_db.call_count == 1  # no second call
            assert mocked_delete_from_backend.call_count == 1
            _, args, kwargs = mocked_delete_from_backend.mock_calls[0]
            assert args[0] == posix_urljoin(
                get_config().hd_backend_api_url, "transformations", str(id_)
            )
            assert kwargs["params"]["ignore_state"] is True

    with caplog.at_level(logging.ERROR):
        resp_mock = mock.Mock()
        resp_mock.status_code = 400
        with mock.patch(
            "hetdesrun.exportimport.utils.requests.delete", return_value=resp_mock
        ) as mocked_delete_from_backend:
            caplog.clear()
            delete_transformation_revision(uuid4())
            assert "COULD NOT DELETE transformation revision with id" in caplog.text

        with mock.patch(
            "hetdesrun.exportimport.utils.delete_single_transformation_revision",
            side_effect=DBNotFoundError,
        ):
            caplog.clear()
            delete_transformation_revision(example_tr_draft, directly_in_db=True)
            assert "Not found error in DB" in caplog.text


def test_delete_transformation_revisions():
    component_operator = example_tr_released.to_operator()
    example_wf_contained = TransformationRevision(
        type=Type.WORKFLOW,
        state=State.DRAFT,
        category="category",
        name="name",
        version_tag="1.0.0",
        description="",
        id=uuid4(),
        revision_group_id=uuid4(),
        io_interface=IOInterface(),
        content=WorkflowContent(operators=[component_operator]),
        documentation="",
        test_wiring=WorkflowWiring(),
    )
    workflow_operator = example_wf_contained.to_operator()
    example_wf_containing = TransformationRevision(
        type=Type.WORKFLOW,
        state=State.DRAFT,
        category="category",
        name="name",
        version_tag="1.0.0",
        description="",
        id=uuid4(),
        revision_group_id=uuid4(),
        io_interface=IOInterface(),
        content=WorkflowContent(operators=[workflow_operator]),
        documentation="",
        test_wiring=WorkflowWiring(),
    )
    with mock.patch(  # noqa: SIM117
        "hetdesrun.exportimport.utils.delete_transformation_revision", return_value=None
    ) as mocked_delete:
        with mock.patch(
            "hetdesrun.exportimport.utils.get_transformation_revisions",
            return_value=[
                example_tr_released,
                example_wf_contained,
                example_wf_containing,
            ],
        ) as mocked_get:
            delete_transformation_revisions(
                [example_tr_released, example_wf_contained, example_wf_containing]
            )
            assert mocked_get.call_count == 1
            _, _, kwargs = mocked_get.mock_calls[0]
            assert kwargs["params"].ids == [
                example_tr_released.id,
                example_wf_contained.id,
                example_wf_containing.id,
            ]
            assert kwargs["params"].include_dependencies is True

            assert mocked_delete.call_count == 3
            _, args, _ = mocked_delete.mock_calls[0]
            assert args[0] == example_wf_containing.id
            _, args, _ = mocked_delete.mock_calls[1]
            assert args[0] == example_wf_contained.id
            _, args, _ = mocked_delete.mock_calls[2]
            assert args[0] == example_tr_released.id


def test_update_or_create_transformation_revision_happy_path():
    with mock.patch(
        "hetdesrun.exportimport.utils.update_or_create_single_transformation_revision",
        return_value=None,
    ) as mocked_update_in_db:
        resp_mock = mock.Mock()
        resp_mock.status_code = 201
        with mock.patch(
            "hetdesrun.exportimport.utils.requests.put", return_value=resp_mock
        ) as mocked_update_in_backend:
            tr_with_updated_tag = deepcopy(example_tr_draft)
            tr_with_updated_tag.version_tag = "1.0.1"
            assert "1.0.1" not in tr_with_updated_tag.content

            update_or_create_transformation_revision(
                tr_with_updated_tag, directly_in_db=True, update_component_code=False
            )
            assert mocked_update_in_db.call_count == 1
            assert mocked_update_in_backend.call_count == 0
            _, args, kwargs = mocked_update_in_db.mock_calls[0]
            assert args[0] == tr_with_updated_tag
            assert kwargs["update_component_code"] is False

            update_or_create_transformation_revision(tr_with_updated_tag, directly_in_db=True)
            assert mocked_update_in_db.call_count == 2
            assert mocked_update_in_backend.call_count == 0
            _, args, kwargs = mocked_update_in_db.mock_calls[1]
            assert args[0] == tr_with_updated_tag
            assert kwargs["update_component_code"] is True
            assert kwargs["strip_wiring"] is False

            update_or_create_transformation_revision(
                tr_with_updated_tag, directly_in_db=True, strip_wiring=True
            )
            assert mocked_update_in_db.call_count == 3
            assert mocked_update_in_backend.call_count == 0
            _, args, kwargs = mocked_update_in_db.mock_calls[2]
            assert args[0] == tr_with_updated_tag
            assert kwargs["strip_wiring"] is True

            update_or_create_transformation_revision(example_tr_draft)
            assert mocked_update_in_db.call_count == 3  # no fourth call
            assert mocked_update_in_backend.call_count == 1
            _, args, kwargs = mocked_update_in_backend.mock_calls[0]
            assert args[0] == posix_urljoin(
                get_config().hd_backend_api_url,
                "transformations",
                str(example_tr_draft.id),
            )
            assert kwargs["params"]["allow_overwrite_released"] is True
            assert kwargs["params"]["update_component_code"] is True
            assert kwargs["params"]["strip_wiring"] is False

            update_or_create_transformation_revision(
                example_tr_draft,
                allow_overwrite_released=False,
                update_component_code=False,
                strip_wiring=True,
            )
            assert mocked_update_in_db.call_count == 3  # no fourth call
            assert mocked_update_in_backend.call_count == 2
            _, args, kwargs = mocked_update_in_backend.mock_calls[1]
            assert args[0] == posix_urljoin(
                get_config().hd_backend_api_url,
                "transformations",
                str(example_tr_draft.id),
            )
            assert kwargs["params"]["allow_overwrite_released"] is False
            assert kwargs["params"]["update_component_code"] is False
            assert kwargs["params"]["strip_wiring"] is True


def test_update_or_create_transformation_revision_rest_api_error(caplog):
    with caplog.at_level(logging.ERROR):
        resp_mock = mock.Mock()
        resp_mock.status_code = 400
        with mock.patch("hetdesrun.exportimport.utils.requests.put", return_value=resp_mock):
            caplog.clear()
            update_or_create_transformation_revision(example_tr_draft)
            assert "COULD NOT PUT" in caplog.text


def test_update_or_create_transformation_revision_rest_api_update_forbidden(caplog):
    with caplog.at_level(logging.INFO):
        resp_mock = mock.Mock()
        resp_mock.status_code = 409
        with mock.patch("hetdesrun.exportimport.utils.requests.put", return_value=resp_mock):
            caplog.clear()
            update_or_create_transformation_revision(
                example_tr_draft, allow_overwrite_released=False
            )
            assert "already in DB and released/deprecated" in caplog.text


def test_update_or_create_transformation_revision_db_not_found(caplog):
    with caplog.at_level(logging.ERROR):  # noqa: SIM117
        with mock.patch(
            "hetdesrun.exportimport.utils.update_or_create_single_transformation_revision",
            side_effect=DBNotFoundError,
        ):
            caplog.clear()
            update_or_create_transformation_revision(example_tr_draft, directly_in_db=True)
            assert "Not found error in DB" in caplog.text


def test_update_or_create_transformation_revision_db_integrity_error(caplog):
    with caplog.at_level(logging.ERROR):  # noqa: SIM117
        with mock.patch(
            "hetdesrun.exportimport.utils.update_or_create_single_transformation_revision",
            side_effect=DBIntegrityError,
        ):
            caplog.clear()
            update_or_create_transformation_revision(example_tr_draft, directly_in_db=True)
            assert "Integrity error in DB" in caplog.text


def test_update_or_create_transformation_revision_db_update_forbidden(caplog):
    with caplog.at_level(logging.INFO):  # noqa: SIM117
        with mock.patch(
            "hetdesrun.exportimport.utils.update_or_create_single_transformation_revision",
            side_effect=ModifyForbidden,
        ):
            caplog.clear()

            with pytest.raises(ModifyForbidden):
                update_or_create_transformation_revision(example_tr_draft, directly_in_db=True)
            assert "Update forbidden for entry" in caplog.text


def test_deprecate_all_but_latest_in_group():
    path = os.path.join(
        "tests",
        "data",
        "components",
        "alerts-from-score_100_38f168ef-cb06-d89c-79b3-0cd823f32e9d.json",
    )
    with open(path) as f:
        import_wf_json = json.load(f)
    import_wf = TransformationRevision(**import_wf_json)
    stored_wf_json = deepcopy(import_wf_json)
    stored_wf_json["id"] = str(uuid4())
    stored_wf_json["version_tag"] = "0.1.0"
    stored_wf_json["released_timestamp"] = datetime.isoformat(
        datetime.fromisoformat(import_wf_json["released_timestamp"]) - timedelta(weeks=1)
    )
    stored_wf = TransformationRevision(**stored_wf_json)
    deprecated_version_of_stored_wf = deepcopy(stored_wf)
    deprecated_version_of_stored_wf.deprecate()
    deprecated_stored_json = json.loads(deprecated_version_of_stored_wf.json())

    with mock.patch(  # noqa: SIM117
        "hetdesrun.exportimport.utils.get_transformation_revisions",
        return_value=[import_wf, stored_wf],
    ) as patched_get:
        with mock.patch(
            "hetdesrun.exportimport.utils.update_or_create_transformation_revision",
            return_value=None,
        ) as patched_update:
            deprecate_all_but_latest_in_group(revision_group_id=import_wf.revision_group_id)

            assert patched_get.call_count == 1

            assert patched_update.call_count == 1
            _, args, _ = patched_update.mock_calls[0]
            update_tr = args[0]
            update_json = json.loads(update_tr.json())
            del update_json["disabled_timestamp"]
            del deprecated_stored_json["disabled_timestamp"]
            assert update_json == deprecated_stored_json

    with mock.patch(  # noqa: SIM117
        "hetdesrun.exportimport.utils.get_transformation_revisions",
        return_value=[],  # no released transformations in group, only deprecated and draft ones
    ) as patched_get:
        with mock.patch(
            "hetdesrun.exportimport.utils.update_or_create_transformation_revision",
            return_value=None,
        ) as patched_update:
            deprecate_all_but_latest_in_group(revision_group_id=stored_wf.revision_group_id)

            assert patched_get.call_count == 1

            assert patched_update.call_count == 0


def test_deprecate_all_but_latest_per_group():
    with mock.patch(
        "hetdesrun.exportimport.purge.deprecate_all_but_latest_in_group",
        return_value=None,
    ) as patched_deprecate_old:
        with mock.patch(
            "hetdesrun.exportimport.purge.get_transformation_revisions",
            return_value=[],
        ) as patched_get:
            deprecate_all_but_latest_per_group()

            assert patched_get.call_count == 1
            _, _, kwargs = patched_get.mock_calls[0]
            assert kwargs["params"].state == State.RELEASED
            assert kwargs["directly_from_db"] is False

            assert patched_deprecate_old.call_count == 0

        with mock.patch(
            "hetdesrun.exportimport.purge.get_transformation_revisions",
            return_value=[example_tr_released_old],
        ) as patched_get:
            deprecate_all_but_latest_per_group()

            assert patched_get.call_count == 1
            _, _, kwargs = patched_get.mock_calls[0]
            assert kwargs["params"].state == State.RELEASED
            assert kwargs["directly_from_db"] is False

            assert patched_deprecate_old.call_count == 1
            _, args, kwargs = patched_deprecate_old.mock_calls[0]
            assert args[0] == example_tr_released_old.revision_group_id
            assert kwargs["directly_in_db"] is False


def test_delete_drafts():
    with mock.patch(
        "hetdesrun.exportimport.purge.delete_transformation_revisions",
        return_value=None,
    ) as mocked_delete:
        with mock.patch(
            "hetdesrun.exportimport.purge.get_transformation_revisions",
            return_value=[],
        ) as patched_get:
            delete_drafts()

            assert patched_get.call_count == 1
            _, _, kwargs = patched_get.mock_calls[0]
            assert kwargs["params"].state == State.DRAFT
            assert kwargs["directly_from_db"] is False

            assert mocked_delete.call_count == 1

        with mock.patch(
            "hetdesrun.exportimport.purge.get_transformation_revisions",
            return_value=[example_tr_draft],
        ) as patched_get:
            delete_drafts()

            assert patched_get.call_count == 1
            _, _, kwargs = patched_get.mock_calls[0]
            assert kwargs["params"].state == State.DRAFT
            assert kwargs["directly_from_db"] is False

            assert mocked_delete.call_count == 2  # one more than before
            _, args, _ = mocked_delete.mock_calls[1]
            assert args[0] == [example_tr_draft]


def test_delete_unused_deprecated():
    with mock.patch(
        "hetdesrun.exportimport.purge.delete_transformation_revisions",
        return_value=None,
    ) as mocked_delete:
        with mock.patch(
            "hetdesrun.exportimport.purge.get_transformation_revisions",
            return_value=[],
        ) as patched_get:
            delete_unused_deprecated()

            assert patched_get.call_count == 1
            _, _, kwargs = patched_get.mock_calls[0]
            assert kwargs["params"].state == State.DISABLED
            assert kwargs["directly_from_db"] is False

            assert mocked_delete.call_count == 1

        with mock.patch(
            "hetdesrun.exportimport.purge.get_transformation_revisions",
            return_value=[example_tr_released_old, example_tr_deprecated],
        ) as patched_get:
            delete_unused_deprecated()

            assert patched_get.call_count == 1
            _, _, kwargs = patched_get.mock_calls[0]
            assert kwargs["params"].state == State.DISABLED
            assert kwargs["directly_from_db"] is False

            assert mocked_delete.call_count == 2  # one more than before
            _, args, _ = mocked_delete.mock_calls[1]
            assert args[0] == [example_tr_released_old, example_tr_deprecated]


def test_delete_all_restart():
    with mock.patch(  # noqa: SIM117
        "hetdesrun.exportimport.purge.delete_transformation_revisions",
        return_value=None,
    ) as mocked_delete:
        with mock.patch(
            "hetdesrun.exportimport.purge.import_transformations",
            return_value=None,
        ) as mocked_import:
            with mock.patch(
                "hetdesrun.exportimport.purge.get_transformation_revisions",
                return_value=[],
            ) as patched_get:
                delete_all_and_refill()

                assert patched_get.call_count == 1
                _, _, kwargs = patched_get.mock_calls[0]
                assert kwargs["directly_from_db"] is False

                assert mocked_delete.call_count == 1

                assert mocked_import.call_count == 1

            with mock.patch(
                "hetdesrun.exportimport.purge.get_transformation_revisions",
                return_value=[
                    example_tr_draft,
                    example_tr_released_old,
                    example_tr_released,
                    example_tr_deprecated,
                ],
            ) as patched_get:
                delete_all_and_refill()

                assert patched_get.call_count == 1
                _, _, kwargs = patched_get.mock_calls[0]
                assert kwargs["directly_from_db"] is False

                assert mocked_delete.call_count == 2  # one more than before
                _, args, kwargs = mocked_delete.mock_calls[1]
                assert args[0] == [
                    example_tr_draft,
                    example_tr_released_old,
                    example_tr_released,
                    example_tr_deprecated,
                ]
                assert kwargs["directly_in_db"] is False

                assert mocked_import.call_count == 2  # one more than before
                _, args, kwargs = mocked_import.mock_calls[0]
                assert args[0] == "./transformations"
                assert kwargs["directly_into_db"] is False
