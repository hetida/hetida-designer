from copy import deepcopy
from unittest import mock
from uuid import UUID, uuid4

import pytest

from hetdesrun.datatypes import DataType
from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.persistence import get_db_engine, sessionmaker
from hetdesrun.persistence.dbmodels import Base
from hetdesrun.persistence.dbservice.exceptions import (
    DBBadRequestError,
    DBIntegrityError,
    DBNotFoundError,
)
from hetdesrun.persistence.dbservice.revision import (
    delete_single_transformation_revision,
    get_latest_revision_id,
    get_multiple_transformation_revisions,
    is_unused,
    read_single_transformation_revision,
    store_single_transformation_revision,
    update_or_create_single_transformation_revision,
)
from hetdesrun.persistence.models.io import (
    IO,
    IOConnector,
    IOInterface,
)
from hetdesrun.persistence.models.link import Link, Vertex
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.persistence.models.workflow import WorkflowContent
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
    patched_session = sessionmaker(clean_test_db_engine)
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        patched_session,
    ):
        with mock.patch(
            "hetdesrun.persistence.dbservice.nesting.Session",
            patched_session,
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

            tr_workflow_uuid = get_uuid_from_seed("workflow")

            tr_workflow = TransformationRevision(
                id=tr_workflow_uuid,
                revision_group_id=tr_workflow_uuid,
                name="Test",
                description="Test description",
                version_tag="1.0.0",
                category="Test category",
                state=State.DRAFT,
                type=Type.WORKFLOW,
                content=WorkflowContent(operators=[tr_released_object.to_operator()]),
                io_interface=IOInterface(),
                test_wiring=WorkflowWiring(),
                documentation="",
            )

            store_single_transformation_revision(tr_draft_object)
            store_single_transformation_revision(tr_released_object)
            update_or_create_single_transformation_revision(tr_workflow)

            delete_single_transformation_revision(tr_draft_uuid)

            with pytest.raises(DBNotFoundError):
                read_single_transformation_revision(tr_draft_uuid)

            with pytest.raises(DBBadRequestError):
                delete_single_transformation_revision(tr_released_uuid)

            # with pytest.raises(DBIntegrityError):
            #     delete_single_transformation_revision(tr_released_uuid, ignore_state=True)

            delete_single_transformation_revision(tr_workflow_uuid, ignore_state=True)
            delete_single_transformation_revision(tr_released_uuid, ignore_state=True)


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
        tr_object_2.category = "Another category"
        tr_object_2.id = tr_uuid_2
        tr_object_2.version_tag = "1.0.1"
        tr_object_2.name = "Test 2"
        store_single_transformation_revision(tr_object_2)

        tr_uuid_3 = get_uuid_from_seed("test_multiple_select_3")
        tr_object_3 = tr_object_template.copy()
        tr_object_3.id = tr_uuid_3
        tr_object_3.revision_group_id = tr_uuid_3
        tr_object_3.release()
        store_single_transformation_revision(tr_object_3)

        results = get_multiple_transformation_revisions()
        assert len(results) == 3

        results = get_multiple_transformation_revisions(state=State.DRAFT)
        assert len(results) == 2

        results = get_multiple_transformation_revisions(state=State.RELEASED)
        assert len(results) == 1

        results = get_multiple_transformation_revisions(revision_group_id=tr_uuid_1)
        assert len(results) == 2

        results = get_multiple_transformation_revisions(type=Type.COMPONENT)
        assert len(results) == 3

        results = get_multiple_transformation_revisions(type=Type.WORKFLOW)
        assert len(results) == 0

        results = get_multiple_transformation_revisions(category="Test category")
        assert len(results) == 2

        results = get_multiple_transformation_revisions(names=["Test"])
        assert len(results) == 2

        results = get_multiple_transformation_revisions(ids=[tr_uuid_3, tr_uuid_2])
        assert len(results) == 2

        results = get_multiple_transformation_revisions(ids=[])
        assert len(results) == 0

        results = get_multiple_transformation_revisions(
            ids=[tr_uuid_3, tr_uuid_2], names=["Test"]
        )
        assert len(results) == 1

        results = get_multiple_transformation_revisions(
            category="Test category", state=State.RELEASED
        )
        assert len(results) == 1

        tr_object_3.deprecate()
        update_or_create_single_transformation_revision(tr_object_3)
        results = get_multiple_transformation_revisions(include_deprecated=False)
        assert len(results) == 2


def test_multiple_select_unused(clean_test_db_engine):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        tr_component_not_contained = TransformationRevision(
            id=uuid4(),
            revision_group_id=uuid4(),
            name="name",
            category="category",
            version_tag="1.0.0",
            type=Type.COMPONENT,
            documentation="",
            state=State.DRAFT,
            content="",
            io_interface=IOInterface(),
            test_wiring=WorkflowWiring(),
        )

        tr_component_contained_only_in_deprecated = deepcopy(tr_component_not_contained)
        tr_component_contained_only_in_deprecated.id = uuid4()
        tr_component_contained_only_in_deprecated.revision_group_id = uuid4()
        tr_component_contained_only_in_deprecated.io_interface = IOInterface(
            outputs=[IO(id=uuid4(), name="o", data_type=DataType.Any)]
        )
        tr_component_contained_only_in_deprecated.release()

        tr_component_contained_not_only_in_deprecated = deepcopy(
            tr_component_contained_only_in_deprecated
        )
        tr_component_contained_not_only_in_deprecated.id = uuid4()
        tr_component_contained_not_only_in_deprecated.revision_group_id = uuid4()

        update_or_create_single_transformation_revision(tr_component_not_contained)
        update_or_create_single_transformation_revision(
            tr_component_contained_only_in_deprecated
        )

        operator_in_deprecated = tr_component_contained_only_in_deprecated.to_operator()
        assert isinstance(operator_in_deprecated.id, UUID)
        output_connector_deprecated = IOConnector(
            id=uuid4(),
            name=operator_in_deprecated.outputs[0].name,
            operator_id=operator_in_deprecated.id,
            connector_id=operator_in_deprecated.outputs[0].id,
            operator_name=operator_in_deprecated.name,
            connector_name=operator_in_deprecated.outputs[0].name,
            data_type=operator_in_deprecated.outputs[0].data_type,
        )
        tr_workflow_deprecated = TransformationRevision(
            id=uuid4(),
            revision_group_id=uuid4(),
            name="name",
            category="category",
            version_tag="1.0.0",
            type=Type.WORKFLOW,
            documentation="",
            state=State.DRAFT,
            content=WorkflowContent(
                operators=[operator_in_deprecated],
                outputs=[output_connector_deprecated],
                links=[
                    Link(
                        id=uuid4(),
                        start=Vertex(
                            operator=operator_in_deprecated.id,
                            connector=operator_in_deprecated.outputs[0],
                        ),
                        end=Vertex(
                            operator=None, connector=output_connector_deprecated
                        ),
                    )
                ],
            ),
            io_interface=IOInterface(),
            test_wiring=WorkflowWiring(),
        )

        operator_in_not_deprecated = (
            tr_component_contained_not_only_in_deprecated.to_operator()
        )
        output_connector_not_deprecated = IOConnector(
            id=uuid4(),
            name=operator_in_not_deprecated.outputs[0].name,
            operator_id=operator_in_not_deprecated.id,
            connector_id=operator_in_not_deprecated.outputs[0].id,
            operator_name=operator_in_not_deprecated.name,
            connector_name=operator_in_not_deprecated.outputs[0].name,
            data_type=operator_in_not_deprecated.outputs[0].data_type,
        )
        tr_workflow_not_deprecated = TransformationRevision(
            id=uuid4(),
            revision_group_id=uuid4(),
            name="name",
            category="category",
            version_tag="1.0.0",
            type=Type.WORKFLOW,
            documentation="",
            state=State.DRAFT,
            content=WorkflowContent(
                operators=[operator_in_not_deprecated],
                outputs=[output_connector_not_deprecated],
                links=[
                    Link(
                        id=uuid4(),
                        start=Vertex(
                            operator=operator_in_not_deprecated.id,
                            connector=operator_in_not_deprecated.outputs[0],
                        ),
                        end=Vertex(
                            operator=None, connector=output_connector_not_deprecated
                        ),
                    )
                ],
            ),
            io_interface=IOInterface(outputs=[output_connector_not_deprecated.to_io()]),
            test_wiring=WorkflowWiring(),
        )

        tr_workflow_deprecated.release()
        tr_workflow_deprecated.deprecate()
        update_or_create_single_transformation_revision(tr_workflow_deprecated)

        tr_workflow_not_deprecated.release()
        update_or_create_single_transformation_revision(tr_workflow_not_deprecated)

        assert is_unused(tr_component_not_contained.id) is True
        assert is_unused(tr_component_contained_only_in_deprecated.id) is True
        assert is_unused(tr_component_contained_not_only_in_deprecated.id) is False

        results = get_multiple_transformation_revisions(
            ids=[tr_component_not_contained.id], unused=True
        )
        assert len(results) == 1

        results = get_multiple_transformation_revisions(
            ids=[tr_component_contained_only_in_deprecated.id], unused=True
        )
        assert len(results) == 1

        results = get_multiple_transformation_revisions(
            ids=[tr_component_contained_not_only_in_deprecated.id], unused=True
        )
        assert len(results) == 0


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
