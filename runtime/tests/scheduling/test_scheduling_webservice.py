import datetime
import os
from uuid import uuid4

import pytest

from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.persistence.models.schedule import Schedule, ScheduledJobState, ScheduleExecution
from hetdesrun.scheduling.execution import execute_scheduled_transformation
from hetdesrun.scheduling.job_sync import sync_job
from hetdesrun.scheduling.retention import executions_retention_job
from hetdesrun.scheduling.scheduler import (
    get_global_scheduler,
)
from hetdesrun.trafoutils.trafo_collection import TrafoCollection


@pytest.mark.asyncio
async def test_schedule_endpoints_with_sync_and_job_execution(  # noqa: PLR0915
    async_test_client, mocked_clean_test_db_session
):
    new_schedule = Schedule(
        id=uuid4(),
        name="Test Schedule 1",
        active=True,
        cron_expression="*/5 * * * *",
        transformation_id="2b1b474f-ddf5-1f4d-fec4-17ef9122112b",
        wiring={"input_wirings": [{"workflow_input_name": "input", "filters": {"value": "test"}}]},
    )

    with TrafoCollection(save_to_db=True) as tc:
        comp_with_funcs = tc.add_from_json_file(  # noqa: F841
            os.path.join(
                "transformations",
                "components",
                "connectors",
                "pass-through-string_100_2b1b474f-ddf5-1f4d-fec4-17ef9122112b.json",
            )
        )

        comp_raising_exception = tc.add_from_py_file(
            os.path.join(
                "tests",
                "data",
                "components",
                "raise_value_error.py",
            )
        )

    async with async_test_client as ac:
        # At beginning: Nothing there
        resp = await ac.get("/api/schedules/", params={})
        assert resp.status_code == 200
        resp_json = resp.json()
        assert len(resp_json) == 0

        # Now add a schedule
        resp = await ac.post("/api/schedules/", json=new_schedule.model_dump(mode="json"))
        assert resp.status_code == 201

        # Check it is there
        resp = await ac.get("/api/schedules/", params={})
        assert resp.status_code == 200
        resp_json = resp.json()
        assert len(resp_json) == 1
        assert resp_json[0]["name"] == "Test Schedule 1"

        # Update
        new_schedule.name = "Renamed"
        resp = await ac.put(
            f"/api/schedules/{str(new_schedule.id)}", json=new_schedule.model_dump(mode="json")
        )
        assert resp.status_code == 201

        # Check updated
        resp = await ac.get("/api/schedules/", params={})
        assert resp.status_code == 200
        resp_json = resp.json()
        assert len(resp_json) == 1
        assert resp_json[0]["name"] == "Renamed"

        # Scheduler not synced yet:
        global_scheduler = get_global_scheduler()
        assert len(global_scheduler.get_jobs()) == 0

        # Sync scheduler and check job is there
        await sync_job()
        assert len(global_scheduler.get_jobs()) == 1

        # There is currently no schedule execution entry:
        resp = await ac.get("/api/schedules/executions", params={})
        assert len(resp.json()) == 0

        # Can run schedule job:
        job_info = await execute_scheduled_transformation("job_" + str(new_schedule.id), "TEST")
        assert job_info.state is ScheduledJobState.SUCCESS
        assert job_info.exec_result.output_results_by_output_name["output"] == "test"

        # There is now a schedule execution entry:
        resp = await ac.get("/api/schedules/executions", params={})
        assert resp.status_code == 200
        executions = resp.json()
        assert len(executions) == 1
        schedule_exec = executions[0]
        assert schedule_exec["schedule_id"] == str(new_schedule.id)

        # Can be found for specific schedule
        resp = await ac.get(
            "/api/schedules/executions", params={"schedule_id": str(new_schedule.id)}
        )
        assert resp.status_code == 200
        executions = resp.json()
        assert len(executions) == 1
        found_schedule_exec = executions[0]
        assert found_schedule_exec["id"] == str(schedule_exec["id"])

        # execution can be obtained explicitely
        resp = await ac.get(f"/api/schedules/executions/{schedule_exec['id']}", params={})
        assert resp.json()["id"] == schedule_exec["id"]
        assert resp.status_code == 200

        # Can be found among all latest schedule executions
        resp = await ac.get("/api/schedules/executions", params={"latest": True})
        assert resp.status_code == 200
        executions = resp.json()
        assert len(executions) == 1
        found_schedule_exec = executions[0]
        assert found_schedule_exec["id"] == str(schedule_exec["id"])

        # Can be found among all latest schedule executions with specified id
        resp = await ac.get(
            "/api/schedules/executions",
            params={"latest": True, "schedule_id": str(new_schedule.id)},
        )
        assert resp.status_code == 200
        executions = resp.json()
        assert len(executions) == 1
        found_schedule_exec = executions[0]
        assert found_schedule_exec["id"] == str(schedule_exec["id"])

        # execution can be obtained as latest execution
        resp = await ac.get(f"/api/schedules/executions/latest/{new_schedule.id}", params={})
        assert resp.status_code == 200
        assert resp.json()["id"] == schedule_exec["id"]

        # set schedule to inactive
        new_schedule.active = False
        resp = await ac.put(
            f"/api/schedules/{new_schedule.id}",
            json=new_schedule.model_dump(mode="json"),
        )
        assert resp.status_code == 201

        # Sync scheduler and check job is not there anymore
        await sync_job()
        assert len(global_scheduler.get_jobs()) == 0

        # set schedule to active again
        new_schedule.active = True
        resp = await ac.put(
            f"/api/schedules/{new_schedule.id}",
            json=new_schedule.model_dump(mode="json"),
        )
        assert resp.status_code == 201

        # Sync scheduler and check job is there again
        await sync_job()
        assert len(global_scheduler.get_jobs()) == 1

        # Change schedule with an existing job
        new_schedule.name = "Renamed again"
        new_schedule.transformation_id = comp_raising_exception.id
        new_schedule.wiring = WorkflowWiring(
            input_wirings=[{"workflow_input_name": "msg", "filters": {"value": "An error occured"}}]
        )

        resp = await ac.put(
            f"/api/schedules/{str(new_schedule.id)}", json=new_schedule.model_dump(mode="json")
        )
        assert resp.status_code == 201

        # Sync scheduler and check job is there again
        await sync_job()
        assert len(global_scheduler.get_jobs()) == 1

        # Can run schedule job:
        job_info = await execute_scheduled_transformation("job_" + str(new_schedule.id), "TEST")
        assert job_info.state is ScheduledJobState.EXECUTION_ERROR
        assert job_info.error_message == "An error occured"

        # Delete schedule
        resp = await ac.delete(f"/api/schedules/{str(new_schedule.id)}")
        assert resp.status_code == 204

        # Check deleted
        resp = await ac.get("/api/schedules/", params={})
        assert resp.status_code == 200
        resp_json = resp.json()
        assert len(resp_json) == 0

        # Sync Scheduler and check job is gone
        await sync_job()
        assert len(global_scheduler.get_jobs()) == 0


@pytest.mark.asyncio
async def test_schedule_execution_endpoints_create_update_delete(  # noqa: PLR0915
    async_test_client, mocked_clean_test_db_session
):
    # Note: That a schedule creates a schedule execution is tested above.

    start_timestamp = datetime.datetime.now(datetime.UTC)

    schedule_exec = ScheduleExecution(
        id=uuid4(),
        schedule_id=uuid4(),
        transformation_id=uuid4(),
        state=ScheduledJobState.STARTED,
        trafo_exec_job_id=uuid4(),
        start=start_timestamp,
        last_state_update=start_timestamp,
    )
    async with async_test_client as ac:
        # Create new via post endpoint

        resp = await ac.post(
            "/api/schedules/executions", json=schedule_exec.model_dump(mode="json")
        )
        assert resp.status_code == 201

        # Can be found
        resp = await ac.get("/api/schedules/executions", params={})
        assert resp.status_code == 200
        executions = resp.json()
        assert len(executions) == 1
        found_schedule_exec = executions[0]
        assert found_schedule_exec["id"] == str(schedule_exec.id)

        # Update
        schedule_exec.state = ScheduledJobState.SUCCESS
        resp = await ac.put(
            f"/api/schedules/executions/{schedule_exec.id}",
            json=schedule_exec.model_dump(mode="json"),
        )
        assert resp.status_code == 201

        # Is now updated
        resp = await ac.get(f"/api/schedules/executions/{schedule_exec.id}", params={})
        assert resp.status_code == 200
        found_schedule_exec = resp.json()
        assert found_schedule_exec["id"] == str(schedule_exec.id)
        assert found_schedule_exec["state"] == str(ScheduledJobState.SUCCESS)

        # delete
        resp = await ac.delete(f"/api/schedules/executions/{schedule_exec.id}", params={})
        assert resp.status_code == 204

        # is now deleted
        resp = await ac.get(f"/api/schedules/executions/{schedule_exec.id}", params={})
        assert resp.status_code == 404

        resp = await ac.get("/api/schedules/executions", params={})
        assert resp.status_code == 200
        executions = resp.json()
        assert len(executions) == 0


@pytest.mark.asyncio
async def test_schedule_execution_retention(  # noqa: PLR0915
    async_test_client, mocked_clean_test_db_session
):
    start_timestamp = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=60)

    schedule_exec = ScheduleExecution(
        id=uuid4(),
        schedule_id=uuid4(),
        transformation_id=uuid4(),
        state=ScheduledJobState.STARTED,
        trafo_exec_job_id=uuid4(),
        start=start_timestamp,
        last_state_update=start_timestamp,
    )
    async with async_test_client as ac:
        # Create new via put endpoint
        resp = await ac.put(
            f"/api/schedules/executions/{schedule_exec.id}",
            json=schedule_exec.model_dump(mode="json"),
        )
        assert resp.status_code == 201

        # is there
        resp = await ac.get(f"/api/schedules/executions/{schedule_exec.id}", params={})
        assert resp.status_code == 200
        found_schedule_exec = resp.json()
        assert found_schedule_exec["id"] == str(schedule_exec.id)

        # call retention job manually
        await executions_retention_job()

        # is not there anymore
        resp = await ac.get(f"/api/schedules/executions/{schedule_exec.id}", params={})
        assert resp.status_code == 404
