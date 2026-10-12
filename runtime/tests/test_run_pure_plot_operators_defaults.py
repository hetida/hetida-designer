"""Test whether pure plot operators are run depending on how an execution is started

See the table in docs/user_guide/component_writing/discarded_outputs.md. That executions from
the user interface run pure plot operators is tested in the frontend.
"""

import importlib
import os
from unittest import mock
from uuid import uuid4

import pytest

from hetdesrun.models.execution import ExecByIdBase, ExecByIdInput, ExecLatestByGroupIdInput
from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.persistence.models.schedule import Schedule, ScheduledJobState
from hetdesrun.scheduling.execution import execute_scheduled_transformation
from hetdesrun.scheduling.job_sync import sync_job
from hetdesrun.trafoutils.trafo_collection import TrafoCollection


def add_logging_plot_component():
    with TrafoCollection(save_to_db=True) as tc:
        return tc.add_from_py_file(os.path.join("tests", "data", "components", "logging_plot.py"))


def test_web_service_and_kafka_executions_do_not_run_pure_plot_operators_by_default():
    # used by the web service endpoints, execution via Kafka and the Kafka consumption mode
    assert ExecByIdBase(id=uuid4()).run_pure_plot_operators is False
    assert ExecByIdInput(id=uuid4()).run_pure_plot_operators is False
    assert (
        ExecLatestByGroupIdInput(
            revision_group_id=uuid4(), wiring=WorkflowWiring()
        ).run_pure_plot_operators
        is False
    )


@pytest.mark.asyncio
async def test_execute_endpoint_does_not_run_pure_plot_operators_by_default(
    mocked_clean_test_db_session, async_test_client
):
    component = add_logging_plot_component()

    async with async_test_client as ac:
        resp = await ac.post("/api/transformations/execute", json={"id": str(component.id)})
        assert resp.status_code == 200
        resp_json = resp.json()
        assert resp_json["error"] is None

        assert resp_json["output_results_by_output_name"]["plot"] == {}
        log_messages = [record["message"] for record in resp_json["gathered_component_code_logs"]]
        assert "Creating plot" not in log_messages


@pytest.mark.asyncio
async def test_schedules_run_pure_plot_operators(mocked_clean_test_db_session, async_test_client):
    component = add_logging_plot_component()
    schedule = Schedule(
        id=uuid4(),
        name="Plot schedule",
        active=True,
        cron_expression="*/5 * * * *",
        transformation_id=component.id,
        wiring=WorkflowWiring(),
    )

    async with async_test_client as ac:
        resp = await ac.post("/api/schedules/", json=schedule.model_dump(mode="json"))
        assert resp.status_code == 201

        await sync_job()
        try:
            job_info = await execute_scheduled_transformation("job_" + str(schedule.id), "TEST")
        finally:
            # remove the job from the global scheduler again
            resp = await ac.delete(f"/api/schedules/{str(schedule.id)}")
            assert resp.status_code == 204
            await sync_job()

    assert job_info.state is ScheduledJobState.SUCCESS
    assert job_info.exec_result.output_results_by_output_name["plot"] != {}


@pytest.mark.asyncio
async def test_dashboards_run_pure_plot_operators(mocked_clean_test_db_session, async_test_client):
    component = add_logging_plot_component()

    # the app imports the router module anew, so this obtains the module actually used
    router_module = importlib.import_module("hetdesrun.backend.service.transformation_router")

    with mock.patch.object(
        router_module,
        "handle_trafo_revision_execution_request",
        wraps=router_module.handle_trafo_revision_execution_request,
    ) as execution_request_spy:
        async with async_test_client as ac:
            resp = await ac.get(f"/api/transformations/{component.id}/dashboard")
            assert resp.status_code == 200

    exec_by_id = execution_request_spy.call_args.args[0]
    assert exec_by_id.run_pure_plot_operators is True
