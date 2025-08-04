import json
import os
from uuid import UUID

import pytest
from pydantic import ValidationError

from hetdesrun.models.execution import ExecByIdInput
from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.persistence.dbservice.exceptions import DBNestingCycleDetected
from hetdesrun.persistence.dbservice.revision import (
    read_single_transformation_revision,
    update_or_create_single_transformation_revision,
)
from hetdesrun.trafoutils.nestings import NestingLevelCycleDetected
from hetdesrun.trafoutils.trafo_collection import TrafoCollection
from hetdesrun.trafoutils.workflow_construction import WorkflowConstructor
from hetdesrun.utils import State


@pytest.mark.asyncio
async def test_draft_trafos_insertable_in_draft_workflow_and_executable(
    mocked_clean_test_db_session, async_test_client
):
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

    workflow_container = wf_container.finalize()

    assert workflow_containee.state is State.DRAFT
    assert workflow_container.state is State.DRAFT

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

    for operator in workflow_container_from_db.content.operators:
        assert operator.state is State.DRAFT

    # execute:
    exec_input = ExecByIdInput(
        id=workflow_container_from_db.id,
        job_id="bbbbbbbb-3cdf-45a4-98ad-bbbbbbbbbbbb",
        wiring=WorkflowWiring(
            input_wirings=[
                {
                    "workflow_input_name": "string_in",
                    "adapter_id": "direct_provisioning",
                    "filters": {"value": "test_string"},
                },
                {
                    "workflow_input_name": "new_input_1",
                    "adapter_id": "direct_provisioning",
                    "filters": {"value": "some_other_test_string"},
                },
            ]
        ),
    )

    async with async_test_client as ac:
        resp = await ac.post(
            "/api/transformations/execute", json=json.loads(exec_input.model_dump_json())
        )
        assert resp.status_code == 200

        resp_json = resp.json()
        assert resp_json["output_results_by_output_name"]["string_out"] == "test_string"


def test_draft_trafos_insertable_in_draft_workflow_in_draft_workflow(mocked_clean_test_db_session):
    """Tests that drafts can be present across several levels"""
    with TrafoCollection(save_to_db=True) as tc:
        log_comp = tc.add_from_py_file(
            os.path.join(
                "tests",
                "data",
                "components",
                "logging_in_component.py",
            )
        )
        with WorkflowConstructor(
            trafo_collector=tc,
            name="Containee",
            version_tag="0.1.0",
            id="3e7c180d-79dd-4416-95f2-185b9e7b36d7",
            auto_release=False,
        ) as wf_containee:
            log_comp = wf_containee.op(log_comp, "log_comp_op")

        tc.add(wf_containee.result)

        with WorkflowConstructor(
            trafo_collector=tc,
            name="Container",
            version_tag="0.1.0",
            id="63667224-e7d6-48e6-b743-e49f66f5c2e5",
            auto_release=False,
        ) as wf_container:
            wf_container.op(wf_containee.result)

        tc.add(wf_container.result)

    assert log_comp.operator.state is State.DRAFT
    assert wf_containee.result.state is State.DRAFT
    assert wf_container.result.state is State.DRAFT


def test_cycle_detection_on_mass_importing(mocked_clean_test_db_session):
    """Mass importing cycle detection test

    TrafoCollection uses mass importing.

    During mass importing, trafos are ordered by their nesting level to
    have all their dependencies imported earlier. Nesting levels would run into
    to infinity if there were no cycle detection.
    """
    with pytest.raises(NestingLevelCycleDetected):  # noqa: PT012, SIM117
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

                with WorkflowConstructor(
                    trafo_collector=tc,
                    name="Container",
                    version_tag="0.1.0",
                    id="63667224-e7d6-48e6-b743-e49f66f5c2e5",
                    auto_release=False,
                ) as wf_container:
                    wf_container.op(workflow_containee)

                    workflow_container = wf_container.finalize()

                wf_containee.op(workflow_container)


def test_cycle_detection_on_storing_single_trafo(mocked_clean_test_db_session):
    """An update introducing a cycle should be detected

    Here update_or_create_single_transformation_revision is used and
    the detection happens in update_nesting.
    """

    # first setup db content without a cycle:

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

            with WorkflowConstructor(
                trafo_collector=tc,
                name="Container",
                version_tag="0.1.0",
                id="63667224-e7d6-48e6-b743-e49f66f5c2e5",
                auto_release=False,
            ) as wf_container:
                wf_container.op(workflow_containee)

                workflow_container = wf_container.finalize()

    # no cycle so far. now add one:
    workflow_containee.content.operators.append(workflow_container.to_operator())

    # try updating the single trafo introducing a cycle:
    with pytest.raises(DBNestingCycleDetected):
        update_or_create_single_transformation_revision(workflow_containee)


def test_releasing_and_deprecating_detects_draft_operators(mocked_clean_test_db_session):
    """Tests that drafts can be present across several levels"""
    with TrafoCollection(save_to_db=False) as tc:
        log_comp = tc.add_from_py_file(
            os.path.join(
                "tests",
                "data",
                "components",
                "logging_in_component.py",
            )
        )
        assert log_comp.state is State.DRAFT

        with WorkflowConstructor(
            trafo_collector=tc,
            name="Containee",
            version_tag="0.1.0",
            id="3e7c180d-79dd-4416-95f2-185b9e7b36d7",
            auto_release=False,
        ) as wf_containee:
            log_comp = wf_containee.op(log_comp, "log_comp_op")

    with pytest.raises(
        ValidationError,
        match="Only a DRAFT Workflow can contain operators instantiating a DRAFT transformation.",
    ):
        wf_containee.result.release()

    with pytest.raises(
        ValidationError,
        match="Only a DRAFT Workflow can contain operators instantiating a DRAFT transformation.",
    ):
        wf_containee.result.deprecate()
