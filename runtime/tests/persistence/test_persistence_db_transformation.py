from unittest import mock

import pytest

from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.persistence import get_db_engine, sessionmaker
from hetdesrun.persistence.dbmodels import Base
from hetdesrun.persistence.dbservice.exceptions import (
    DBBadRequestError,
    DBNotFoundError,
)
from hetdesrun.persistence.dbservice.revision import (
    delete_single_transformation_revision,
    get_latest_revision_id,
    read_single_transformation_revision,
    select_multiple_transformation_revisions,
    store_single_transformation_revision,
    update_or_create_single_transformation_revision,
)
from hetdesrun.persistence.models.io import IOInterface
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.utils import State, Type, get_uuid_from_seed


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


def test_storing_and_receiving(clean_test_db_engine):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        tr_uuid = get_uuid_from_seed("test_storing_and_receiving")

        tr_object = TransformationRevision(
            id=tr_uuid,
            revision_group_id=tr_uuid,
            name="Test",
            description="Test description",
            version_tag="1.0.0",
            category="Test category",
            state=State.DRAFT,
            type=Type.COMPONENT,
            content="code",
            io_interface=IOInterface(),
            test_wiring=WorkflowWiring(),
            documentation="",
        )

        store_single_transformation_revision(tr_object)

        received_tr_object = read_single_transformation_revision(tr_uuid)

        assert tr_object == received_tr_object

        # non-existent object
        wrong_tr_uuid = get_uuid_from_seed("wrong id")
        with pytest.raises(DBNotFoundError):
            received_tr_object = read_single_transformation_revision(wrong_tr_uuid)


def test_updating(clean_test_db_engine):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        tr_uuid = get_uuid_from_seed("test_updating")

        tr_object = TransformationRevision(
            id=tr_uuid,
            revision_group_id=tr_uuid,
            name="Test",
            description="Test description",
            version_tag="1.0.0",
            category="Test category",
            state=State.DRAFT,
            type=Type.COMPONENT,
            content="code",
            io_interface=IOInterface(),
            test_wiring=WorkflowWiring(),
            documentation="",
        )

        store_single_transformation_revision(tr_object)

        tr_object.name = "Test Update"

        update_or_create_single_transformation_revision(tr_object)

        received_tr_object = read_single_transformation_revision(tr_uuid)

        assert tr_object == received_tr_object


def test_creating(clean_test_db_engine):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        tr_uuid = get_uuid_from_seed("test_creating")

        tr_object = TransformationRevision(
            id=tr_uuid,
            revision_group_id=tr_uuid,
            name="Test",
            description="Test description",
            version_tag="1.0.0",
            category="Test category",
            state=State.DRAFT,
            type=Type.COMPONENT,
            content="code",
            io_interface=IOInterface(),
            test_wiring=WorkflowWiring(),
            documentation="",
        )

        update_or_create_single_transformation_revision(tr_object)

        received_tr_object = read_single_transformation_revision(tr_uuid)

        assert tr_object == received_tr_object


def test_deleting(clean_test_db_engine):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        tr_draft_uuid = get_uuid_from_seed("draft")

        tr_draft_object = TransformationRevision(
            id=tr_draft_uuid,
            revision_group_id=tr_draft_uuid,
            name="Test",
            description="Test description",
            version_tag="1.0.0",
            category="Test category",
            state=State.DRAFT,
            type=Type.COMPONENT,
            content="code",
            io_interface=IOInterface(),
            test_wiring=WorkflowWiring(),
            documentation="",
        )

        tr_released_uuid = get_uuid_from_seed("released")

        tr_released_object = TransformationRevision(
            id=tr_released_uuid,
            revision_group_id=tr_released_uuid,
            name="Test",
            description="Test description",
            version_tag="1.0.0",
            category="Test category",
            released_timestamp="2021-12-24 00:00",
            state=State.RELEASED,
            type=Type.COMPONENT,
            content="code",
            io_interface=IOInterface(),
            test_wiring=WorkflowWiring(),
            documentation="",
        )

        store_single_transformation_revision(tr_draft_object)
        store_single_transformation_revision(tr_released_object)

        delete_single_transformation_revision(tr_draft_uuid)

        with pytest.raises(DBNotFoundError):
            read_single_transformation_revision(tr_draft_uuid)

        with pytest.raises(DBBadRequestError):
            delete_single_transformation_revision(tr_released_uuid)


def test_multiple_select(clean_test_db_engine):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        tr_template_id = get_uuid_from_seed("object_template")
        tr_object_template = TransformationRevision(
            id=tr_template_id,
            revision_group_id=tr_template_id,
            name="Test",
            description="Test description",
            version_tag="1.0.0",
            category="Test category",
            state=State.DRAFT,
            type=Type.COMPONENT,
            content="code",
            io_interface=IOInterface(),
            test_wiring=WorkflowWiring(),
            documentation="",
        )

        tr_uuid_1 = get_uuid_from_seed("test_multiple_select_1")
        tr_object_1 = tr_object_template.copy()
        tr_object_1.id = tr_uuid_1
        tr_object_1.revision_group_id = tr_uuid_1
        store_single_transformation_revision(tr_object_1)

        tr_uuid_2 = get_uuid_from_seed("test_multiple_select_2")
        tr_object_2 = tr_object_1.copy()
        tr_object_2.id = tr_uuid_2
        tr_object_2.version_tag = "1.0.1"
        store_single_transformation_revision(tr_object_2)

        tr_object_3 = tr_object_template.copy()
        tr_uuid_3 = get_uuid_from_seed("test_multiple_select_3")
        tr_object_3.id = tr_uuid_3
        tr_object_3.revision_group_id = tr_uuid_3
        tr_object_3.release()
        store_single_transformation_revision(tr_object_3)

        results = select_multiple_transformation_revisions()
        assert len(results) == 3

        results = select_multiple_transformation_revisions(state=State.DRAFT)
        assert len(results) == 2

        results = select_multiple_transformation_revisions(state=State.RELEASED)
        assert len(results) == 1

        results = select_multiple_transformation_revisions(revision_group_id=tr_uuid_1)
        assert len(results) == 2

        results = select_multiple_transformation_revisions(type=Type.COMPONENT)
        assert len(results) == 3

        results = select_multiple_transformation_revisions(type=Type.WORKFLOW)
        assert len(results) == 0

        # TODO: Test more cases: E.g. Combined filters


def test_get_latest_revision_id(clean_test_db_engine):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        tr_template_id = get_uuid_from_seed("object_template")
        tr_object_template = TransformationRevision(
            id=get_uuid_from_seed("test_get_latest_revision_0"),
            revision_group_id=tr_template_id,
            name="Test",
            description="Test description",
            version_tag="1.0.0",
            category="Test category",
            state=State.DRAFT,
            type=Type.COMPONENT,
            content="code",
            io_interface=IOInterface(),
            test_wiring=WorkflowWiring(),
            documentation="",
        )

        tr_object_1 = tr_object_template.copy()
        tr_object_1.id = get_uuid_from_seed("test_get_latest_revision_1")
        tr_object_1.version_tag = "1.0.1"
        tr_object_1.release()
        store_single_transformation_revision(tr_object_1)

        tr_object_2 = tr_object_template.copy()
        tr_object_2.id = get_uuid_from_seed("test_get_latest_revision_2")
        tr_object_2.version_tag = "1.0.2"
        tr_object_2.release()
        store_single_transformation_revision(tr_object_2)

        assert get_latest_revision_id(tr_template_id) == get_uuid_from_seed(
            "test_get_latest_revision_2"
        )
