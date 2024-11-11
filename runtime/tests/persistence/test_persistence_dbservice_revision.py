from copy import deepcopy
from sqlite3 import Connection as SQLite3Connection
from uuid import UUID, uuid4

import pytest
from sqlalchemy import event
from sqlalchemy.future.engine import Engine

from hetdesrun.datatypes import DataType
from hetdesrun.models.wiring import InputWiring, WorkflowWiring
from hetdesrun.persistence.dbservice.exceptions import DBIntegrityError, DBNotFoundError
from hetdesrun.persistence.dbservice.revision import (
    delete_single_transformation_revision,
    get_latest_revision_id,
    get_multiple_transformation_revisions,
    is_modifiable,
    is_unused,
    read_single_transformation_revision,
    store_single_transformation_revision,
    update_or_create_single_transformation_revision,
)
from hetdesrun.persistence.models.exceptions import StateConflict, TypeConflict
from hetdesrun.persistence.models.io import (
    IOInterface,
    TransformationInput,
    TransformationOutput,
    WorkflowContentOutput,
)
from hetdesrun.persistence.models.link import Link, Vertex
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.persistence.models.workflow import WorkflowContent
from hetdesrun.trafoutils.filter.params import FilterParams
from hetdesrun.utils import State, Type, get_uuid_from_seed


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection: SQLite3Connection, connection_record) -> None:  # type: ignore  # noqa: E501,
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def test_storing_and_receiving(mocked_clean_test_db_session):
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


def test_is_modifiable():
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

    changed_type_tr = deepcopy(tr_object)
    changed_type_tr.type = Type.WORKFLOW
    assert (
        is_modifiable(
            existing_transformation_revision=tr_object,
            updated_transformation_revision=changed_type_tr,
        )[0]
        is False
    )

    changed_name_tr = deepcopy(tr_object)
    changed_name_tr.name = "Name"
    assert (
        is_modifiable(
            existing_transformation_revision=tr_object,
            updated_transformation_revision=changed_name_tr,
        )[0]
        is True
    )

    tr_object.release()
    changed_name_released_tr = deepcopy(tr_object)
    changed_name_released_tr.name = "Other name"
    assert (
        is_modifiable(
            existing_transformation_revision=tr_object,
            updated_transformation_revision=changed_name_released_tr,
        )[0]
        is False
    )
    assert (
        is_modifiable(
            existing_transformation_revision=tr_object,
            updated_transformation_revision=changed_name_released_tr,
            allow_overwrite_released=True,
        )[0]
        is True
    )

    deprecated_tr = deepcopy(tr_object)
    deprecated_tr.deprecate()
    assert (
        is_modifiable(
            existing_transformation_revision=tr_object,
            updated_transformation_revision=deprecated_tr,
        )[0]
        is True
    )
    assert (
        is_modifiable(
            existing_transformation_revision=deprecated_tr,
            updated_transformation_revision=tr_object,
        )[0]
        is False
    )
    assert (
        is_modifiable(
            existing_transformation_revision=deprecated_tr,
            updated_transformation_revision=tr_object,
            allow_overwrite_released=True,
        )[0]
        is True
    )


def test_updating(mocked_clean_test_db_session):
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

    received_tr_object = update_or_create_single_transformation_revision(
        tr_object, update_component_code=False
    )
    assert received_tr_object.content == "code"
    assert tr_object == received_tr_object

    tr_object.io_interface = IOInterface(
        inputs=[TransformationInput(name="input", data_type=DataType.Integer)]
    )
    tr_object.test_wiring = WorkflowWiring(
        input_wirings=[
            InputWiring(
                workflow_input_name="input",
                adapter_id="direct_provisioning",
                filters={"value": 5},
            )
        ]
    )
    received_tr_object = update_or_create_single_transformation_revision(tr_object)
    assert "COMPONENT_INFO" in received_tr_object.content
    assert len(received_tr_object.test_wiring.input_wirings) == 1


def test_strip_wirings_and_keep_only_wirings(mocked_clean_test_db_session):
    tr_uuid = get_uuid_from_seed("test_strip_wirings_and_keep_only_wirings")

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

    tr_object.io_interface = IOInterface(
        inputs=[
            TransformationInput(name="input", data_type=DataType.Integer),
            TransformationInput(name="input2", data_type=DataType.Integer),
        ]
    )
    tr_object.test_wiring = WorkflowWiring(
        input_wirings=[
            InputWiring(
                workflow_input_name="input",
                adapter_id="direct_provisioning",
                filters={"value": 5},
            ),
            InputWiring(
                ref_id="some_ref_id",
                workflow_input_name="input2",
                adapter_id="blah",
                filters={"value": 5},
            ),
        ]
    )

    # Test strip_wiring
    received_tr_object = update_or_create_single_transformation_revision(
        tr_object.copy(deep=True), strip_wiring=True
    )
    assert len(received_tr_object.test_wiring.input_wirings) == 0

    # Test strip_wirings_with_adapter_ids
    received_tr_object = update_or_create_single_transformation_revision(
        tr_object.copy(deep=True),
        strip_wiring=False,
        strip_wirings_with_adapter_ids={"blubb", "blah"},
    )
    assert len(received_tr_object.test_wiring.input_wirings) == 1
    assert received_tr_object.test_wiring.input_wirings[0].adapter_id == "direct_provisioning"

    # Test keep_only_wirings_with_adapter_ids

    received_tr_object = update_or_create_single_transformation_revision(
        tr_object.copy(deep=True),
        strip_wiring=False,
        keep_only_wirings_with_adapter_ids={"blubb", "blah"},
    )
    assert len(received_tr_object.test_wiring.input_wirings) == 1
    assert received_tr_object.test_wiring.input_wirings[0].adapter_id == "blah"


def test_strip_release_wirings_and_keep_only_release_wirings(mocked_clean_test_db_session):
    tr_uuid = get_uuid_from_seed("test_strip_release_wirings_and_keep_only_release_wirings")

    tr_object = TransformationRevision(
        id=tr_uuid,
        revision_group_id=tr_uuid,
        name="Test",
        description="Test description",
        version_tag="1.0.0",
        category="Test category",
        state=State.RELEASED,
        type=Type.COMPONENT,
        content="code",
        io_interface=IOInterface(),
        test_wiring=WorkflowWiring(),
        release_wiring=WorkflowWiring(),
        released_timestamp="2024-09-05T11:56:00+00:00",
        documentation="",
    )

    store_single_transformation_revision(tr_object)

    tr_object.name = "Test Update"

    tr_object.io_interface = IOInterface(
        inputs=[
            TransformationInput(name="input", data_type=DataType.Integer),
            TransformationInput(name="input2", data_type=DataType.Integer),
        ]
    )
    tr_object.release_wiring = WorkflowWiring(
        input_wirings=[
            InputWiring(
                workflow_input_name="input",
                adapter_id="direct_provisioning",
                filters={"value": 5},
            ),
            InputWiring(
                ref_id="some_ref_id",
                workflow_input_name="input2",
                adapter_id="blah",
                filters={"value": 5},
            ),
        ]
    )

    # Test strip_wiring
    received_tr_object = update_or_create_single_transformation_revision(
        tr_object.copy(deep=True), strip_release_wiring=True, allow_overwrite_released=True
    )
    assert received_tr_object.release_wiring is None

    # Test strip_wirings_with_adapter_ids
    received_tr_object = update_or_create_single_transformation_revision(
        tr_object.copy(deep=True),
        strip_release_wiring=False,
        strip_release_wirings_with_adapter_ids={"blubb", "blah"},
        allow_overwrite_released=True,
    )
    assert len(received_tr_object.release_wiring.input_wirings) == 1
    assert received_tr_object.release_wiring.input_wirings[0].adapter_id == "direct_provisioning"

    # Test keep_only_wirings_with_adapter_ids

    received_tr_object = update_or_create_single_transformation_revision(
        tr_object.copy(deep=True),
        strip_release_wiring=False,
        keep_only_release_wirings_with_adapter_ids={"blubb", "blah"},
        allow_overwrite_released=True,
    )
    assert len(received_tr_object.release_wiring.input_wirings) == 1
    assert received_tr_object.release_wiring.input_wirings[0].adapter_id == "blah"


def test_creating(mocked_clean_test_db_session):
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


def test_deleting(mocked_clean_test_db_session):
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

    with pytest.raises(StateConflict):
        delete_single_transformation_revision(tr_released_uuid)

    with pytest.raises(TypeConflict):
        delete_single_transformation_revision(tr_workflow_uuid, type=Type.COMPONENT)

    with pytest.raises(DBIntegrityError):
        delete_single_transformation_revision(tr_released_uuid, ignore_state=True)

    delete_single_transformation_revision(tr_workflow_uuid, ignore_state=True)
    delete_single_transformation_revision(tr_released_uuid, ignore_state=True)


def test_multiple_select(mocked_clean_test_db_session):  # noqa: PLR0915
    # TODO: restructure this test to properly solve too many statements issue
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

    results = get_multiple_transformation_revisions(FilterParams())
    assert len(results) == 3

    results = get_multiple_transformation_revisions(FilterParams(state=State.DRAFT))
    assert len(results) == 2

    results = get_multiple_transformation_revisions(
        FilterParams(state=State.RELEASED, include_dependencies=False)
    )
    assert len(results) == 1

    results = get_multiple_transformation_revisions(
        FilterParams(revision_group_id=tr_uuid_1, include_dependencies=False)
    )
    assert len(results) == 2

    results = get_multiple_transformation_revisions(
        FilterParams(type=Type.COMPONENT, include_dependencies=False)
    )
    assert len(results) == 3

    results = get_multiple_transformation_revisions(
        FilterParams(type=Type.WORKFLOW, include_dependencies=False)
    )
    assert len(results) == 0

    results = get_multiple_transformation_revisions(
        FilterParams(categories=["Test category"], include_dependencies=False)
    )
    assert len(results) == 2

    results = get_multiple_transformation_revisions(
        FilterParams(category_prefix="Test cat", include_dependencies=False)
    )
    assert len(results) == 2

    results = get_multiple_transformation_revisions(
        FilterParams(names=["Test"], include_dependencies=False)
    )
    assert len(results) == 2

    results = get_multiple_transformation_revisions(
        FilterParams(ids=[tr_uuid_3, tr_uuid_2], include_dependencies=False)
    )
    assert len(results) == 2

    results = get_multiple_transformation_revisions(
        FilterParams(ids=[], include_dependencies=False)
    )
    assert len(results) == 0

    results = get_multiple_transformation_revisions(
        FilterParams(ids=[tr_uuid_3, tr_uuid_2], names=["Test"], include_dependencies=False)
    )
    assert len(results) == 1

    results = get_multiple_transformation_revisions(
        FilterParams(
            categories=["Test category"],
            state=State.RELEASED,
            include_dependencies=False,
        )
    )
    assert len(results) == 1

    tr_object_3.deprecate()
    update_or_create_single_transformation_revision(tr_object_3)
    results = get_multiple_transformation_revisions(
        FilterParams(include_deprecated=False, include_dependencies=False)
    )
    assert len(results) == 2


def test_multiple_select_unused(mocked_clean_test_db_session):
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
        outputs=[TransformationOutput(id=uuid4(), name="o", data_type=DataType.Any)]
    )
    tr_component_contained_only_in_deprecated.release()

    tr_component_contained_not_only_in_deprecated = deepcopy(
        tr_component_contained_only_in_deprecated
    )
    tr_component_contained_not_only_in_deprecated.id = uuid4()
    tr_component_contained_not_only_in_deprecated.revision_group_id = uuid4()

    update_or_create_single_transformation_revision(tr_component_not_contained)
    update_or_create_single_transformation_revision(tr_component_contained_only_in_deprecated)
    update_or_create_single_transformation_revision(tr_component_contained_not_only_in_deprecated)

    operator_in_deprecated = tr_component_contained_only_in_deprecated.to_operator()
    assert isinstance(operator_in_deprecated.id, UUID)
    output_connector_deprecated = WorkflowContentOutput(
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
                    end=Vertex(operator=None, connector=output_connector_deprecated),
                )
            ],
        ),
        io_interface=IOInterface(),
        test_wiring=WorkflowWiring(),
    )

    operator_in_not_deprecated = tr_component_contained_not_only_in_deprecated.to_operator()
    output_connector_not_deprecated = WorkflowContentOutput(
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
                    end=Vertex(operator=None, connector=output_connector_not_deprecated),
                )
            ],
        ),
        io_interface=IOInterface(
            outputs=[TransformationOutput(**output_connector_not_deprecated.dict())]
        ),
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
        FilterParams(
            ids=[tr_component_not_contained.id],
            unused=True,
            include_dependencies=False,
        )
    )
    assert len(results) == 1

    results = get_multiple_transformation_revisions(
        FilterParams(
            ids=[tr_component_contained_only_in_deprecated.id],
            unused=True,
            include_dependencies=False,
        )
    )
    assert len(results) == 1

    results = get_multiple_transformation_revisions(
        FilterParams(
            ids=[tr_component_contained_not_only_in_deprecated.id],
            unused=True,
            include_dependencies=False,
        )
    )
    assert len(results) == 0


def test_get_latest_revision_id(mocked_clean_test_db_session):
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
