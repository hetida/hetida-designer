import os
from uuid import uuid4

import pytest

from hetdesrun.persistence.models.schedule import Schedule, ScheduledJobState
from hetdesrun.scheduling import execute_scheduled_transformation, get_global_scheduler, sync_job
from hetdesrun.trafoutils.trafo_collection import TrafoCollection


@pytest.mark.asyncio
async def test_schedule_endpoints_with_sync_and_job_execution(
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

        # Scheduler not synced yet:
        global_scheduler = get_global_scheduler()
        assert len(global_scheduler.get_jobs()) == 0

        # Sync scheduler and check job is there
        await sync_job()
        assert len(global_scheduler.get_jobs()) == 1

        # Can run schedule job:
        job_info = await execute_scheduled_transformation("job_" + str(new_schedule.id), "TEST")
        assert job_info.state is ScheduledJobState.SUCCESS
        assert job_info.exec_result.output_results_by_output_name["output"] == "test"

        # Check updated
        resp = await ac.get("/api/schedules/", params={})
        assert resp.status_code == 200
        resp_json = resp.json()
        assert len(resp_json) == 1
        assert resp_json[0]["name"] == "Renamed"

        # Delete
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
