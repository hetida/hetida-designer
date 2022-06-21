from unittest import mock

import pytest

from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.persistence import get_db_engine, sessionmaker
from hetdesrun.persistence.dbmodels import Base
from hetdesrun.persistence.dbservice.nesting import update_or_create_nesting
from hetdesrun.persistence.dbservice.revision import (
    store_single_transformation_revision,
)
from hetdesrun.persistence.models.io import IO, IOInterface
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.persistence.models.workflow import WorkflowContent
from hetdesrun.utils import get_uuid_from_seed


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


def component_creator(identifier: str) -> TransformationRevision:
    tr_component = TransformationRevision(
        id=get_uuid_from_seed("component " + identifier),
        revision_group_id=get_uuid_from_seed("group of component " + identifier),
        name=identifier,
        type="COMPONENT",
        state="DRAFT",
        version_tag="1.0.0",
        io_interface=IOInterface(),
        content="code",
        test_wiring=WorkflowWiring(),
    )
    return tr_component


def workflow_creator(identifier: str) -> TransformationRevision:
    tr_workflow = TransformationRevision(
        id=get_uuid_from_seed("workflow " + identifier),
        revision_group_id=get_uuid_from_seed("group of workflow " + identifier),
        name=identifier,
        type="WORKFLOW",
        state="DRAFT",
        version_tag="1.0.0",
        io_interface=IOInterface(),
        content=WorkflowContent(),
        test_wiring=WorkflowWiring(),
    )
    return tr_workflow


# @pytest.mark.skip
def test_update_or_create_nesting(clean_test_db_engine):
    patched_session = sessionmaker(clean_test_db_engine)
    with mock.patch(
        "hetdesrun.persistence.dbservice.nesting.Session",
        patched_session,
    ):
        with mock.patch(
            "hetdesrun.persistence.dbservice.revision.Session",
            patched_session,
        ):
            component_a = component_creator("a")
            component_a.io_interface.inputs.append(
                IO(name="component_a_input", data_type="INT")
            )
            component_a.io_interface.outputs.append(
                IO(name="component_a_output", data_type="INT")
            )
            component_a.release()
            store_single_transformation_revision(component_a)

            component_b = component_creator("b")
            component_b.io_interface.inputs.append(
                IO(name="component_b_input", data_type="INT")
            )
            component_b.io_interface.outputs.append(
                IO(name="component_b_output", data_type="INT")
            )
            component_b.release()
            store_single_transformation_revision(component_b)

            workflow_sister = workflow_creator("sister")
            workflow_sister.content = WorkflowContent(
                operators=[component_a.to_operator()]
            )
            store_single_transformation_revision(workflow_sister)
            update_or_create_nesting(workflow_sister)

            workflow_brother = workflow_creator("brother")
            workflow_brother.content.operators.append(component_a.to_operator())
            workflow_brother.content.operators.append(component_b.to_operator())
            store_single_transformation_revision(workflow_brother)
            update_or_create_nesting(workflow_brother)

            workflow_parent = workflow_creator("parent")
            workflow_parent.content.operators.append(component_a.to_operator())
            store_single_transformation_revision(workflow_parent)
            update_or_create_nesting(workflow_parent)

            # workflow_sister.io_interface.inputs[0].name = "name"
            workflow_sister.release()
            workflow_parent.content.operators.append(workflow_sister.to_operator())
            update_or_create_nesting(workflow_parent)

            workflow_brother.release()
            workflow_parent.content.operators.append(workflow_brother.to_operator())
            update_or_create_nesting(workflow_parent)

            workflow_ancestor = workflow_creator("ancestor")
            workflow_parent.release()
            workflow_ancestor.content.operators.append(workflow_parent.to_operator())
            store_single_transformation_revision(workflow_ancestor)
            update_or_create_nesting(workflow_ancestor)
