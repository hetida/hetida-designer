import os
from uuid import UUID

import pytest

from hetdesrun.persistence.dbservice.revision import (
    read_single_transformation_revision,
    update_or_create_single_transformation_revision,
)
from hetdesrun.trafoutils.trafo_collection import TrafoCollection
from hetdesrun.trafoutils.upgrade_operators import upgrade_operators_in_workflow
from hetdesrun.trafoutils.workflow_construction import WorkflowConstructor
from hetdesrun.utils import State


@pytest.mark.asyncio
async def test_draft_operator_upgrading(mocked_clean_test_db_session, async_test_client):
    """Checks that upgrading draft operators to their current db version works"""
    with TrafoCollection(save_to_db=True) as tc:
        pt_string = tc.add_from_json_file(
            os.path.join(
                "transformations",
                "components",
                "connectors",
                "pass-through-string_100_2b1b474f-ddf5-1f4d-fec4-17ef9122112b.json",
            )
        )

        with WorkflowConstructor(
            trafo_collector=tc,
            name="Containee",
            version_tag="0.1.0",
            id="3e7c180d-79dd-4416-95f2-185b9e7b36d7",
            auto_release=False,
        ) as wf_containee:
            string_op = wf_containee.op(pt_string, "string_pass_through")
            wf_containee.input("string_in", string_op.i["input"])
            wf_containee.output("string_out", string_op.o["output"])

    workflow_containee = wf_containee.finalize()

    with TrafoCollection(save_to_db=True) as tc:  # noqa: SIM117
        log_comp = tc.add_from_py_file(
            os.path.join(
                "tests",
                "data",
                "components",
                "logging_in_component.py",
            )
        )
        assert log_comp.state is State.DRAFT

        tc.add(workflow_containee)

        with WorkflowConstructor(
            trafo_collector=tc,
            name="Container",
            version_tag="0.1.0",
            id="63667224-e7d6-48e6-b743-e49f66f5c2e5",
            auto_release=False,
        ) as wf_container:
            containee_op = wf_container.op(workflow_containee)
            log_op = wf_container.op(log_comp)
            wf_container.input("string_in", containee_op.i["string_in"])
            wf_container.output("string_out", containee_op.o["string_out"])
            wf_container.input("new_input_1", log_op.i["new_input_1"])
            wf_container.output("exec_context", log_op.o["exec_context"])
            wf_container.output("dunder_name", log_op.o["dunder_name"])
            wf_container.output("logger_filters", log_op.o["logger_filters"])
            wf_container.output("logger_name", log_op.o["logger_name"])

    workflow_containee_from_db = read_single_transformation_revision(
        UUID("3e7c180d-79dd-4416-95f2-185b9e7b36d7")
    )  # is in db
    workflow_container_from_db = read_single_transformation_revision(
        UUID("63667224-e7d6-48e6-b743-e49f66f5c2e5")
    )  # is in db
    logging_component_from_db = read_single_transformation_revision(
        UUID("abafbb92-3cdf-45a4-98ad-c72d9cf0b705")
    )  # is in db

    assert workflow_containee_from_db.state is State.DRAFT
    assert workflow_container_from_db.state is State.DRAFT
    assert logging_component_from_db.state is State.DRAFT

    assert len(workflow_container_from_db.content.operators) == 2
    assert (
        len([op for op in workflow_container_from_db.content.operators if op.state is State.DRAFT])
        == 2
    )

    # make changes
    workflow_containee_from_db.version_tag = "changed_version_tag"
    update_or_create_single_transformation_revision(
        transformation_revision=workflow_containee_from_db
    )

    log_comp.release()
    update_or_create_single_transformation_revision(log_comp)

    upgraded_wf = upgrade_operators_in_workflow(
        workflow_container_from_db, only_check_deprecated=False
    )

    assert len(upgraded_wf.content.operators) == 2

    # updated simple change in containee draft:
    assert (
        len([op for op in upgraded_wf.content.operators if op.version_tag == "changed_version_tag"])
        == 1
    )
    # updated component operator to new released state
    assert len([op for op in upgraded_wf.content.operators if op.state is State.RELEASED]) == 1
