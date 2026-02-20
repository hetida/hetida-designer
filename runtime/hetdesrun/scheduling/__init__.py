import asyncio
import datetime
import functools
import logging
import threading
import time
from uuid import uuid4

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from hetdesrun.backend.execution import (
    TrafoExecutionComponentAdapterComponentsNotFound,
    TrafoExecutionComponentImportCycleError,
    TrafoExecutionComponentImportsLoadingError,
    TrafoExecutionInputValidationError,
    TrafoExecutionNotFoundError,
    TrafoExecutionResultValidationError,
    TrafoExecutionRuntimeConnectionError,
    TrafoExecutionRuntimeHttpStatusError,
    perf_measured_execute_trafo_rev,
)
from hetdesrun.component.load import ComponentImportCycleError
from hetdesrun.models.execution import ExecByIdInput
from hetdesrun.persistence.dbservice.schedule import get_multiple_schedules
from hetdesrun.persistence.models.schedule import (
    Schedule,
    ScheduledJobInformation,
    ScheduledJobState,
)
from hetdesrun.webservice.config import get_config

logger = logging.getLogger(__name__)


@functools.cache
def get_global_scheduler() -> AsyncIOScheduler:
    logger.debug("First initialization of scheduler object")
    return AsyncIOScheduler()


@functools.cache
def get_global_schedule_infos() -> dict[str, Schedule]:
    """Stores additional information to the APScheduler jobs

    We store the actual Schedule object for each apscheduler job in order to
    determine if something changed and the job needs to be rescheduled
    """
    return {}


async def execute_scheduled_transformation(job_id: str, name: str) -> None:  # noqa: PLR0915 PLR0912
    """Execution of scheduled transformation revisions job function"""
    schedule = get_global_schedule_infos().get(job_id, None)

    if schedule is None:
        logger.error(
            "Missing schedule object for job %s with name %s. Cannot run. Aborting.", job_id, name
        )
        return

    if schedule.transformation_id is None:
        logger.error(
            "Missing schedule object for job %s with name %s. Cannot run. Aborting.", job_id, name
        )
        return

    exec_job_id = uuid4()
    exec_by_id = ExecByIdInput(
        job_id=exec_job_id,
        id=schedule.transformation_id,
        wiring=schedule.wiring,
        run_pure_plot_operators=False,
    )

    scheduled_job_info = ScheduledJobInformation(
        state=ScheduledJobState.STARTED,
        schedule_job_id=str(job_id),
        schedule_name=name,
        trafo_exec_job_id=str(exec_job_id),
    )

    try:
        exec_result = await perf_measured_execute_trafo_rev(exec_by_id)
    except TrafoExecutionInputValidationError as err:
        msg = (
            "Could not validate execution input"
            f"\n{exec_by_id.model_dump_json(indent=2)}:\n{str(err)}"
        )
        scheduled_job_info.state = ScheduledJobState.INVOCATION_ERROR
        scheduled_job_info.error_message = msg
        logger.error(msg)

    except TrafoExecutionNotFoundError as err:
        msg = f"Could not find transformation revision {exec_by_id.id}:\n{str(err)}"
        scheduled_job_info.state = ScheduledJobState.INVOCATION_ERROR
        scheduled_job_info.error_message = msg
        logger.error(msg)

    except (ComponentImportCycleError, TrafoExecutionComponentImportCycleError) as err:
        msg = f"Detected component import cycle:\n{str(err)}"
        scheduled_job_info.state = ScheduledJobState.INVOCATION_ERROR
        scheduled_job_info.error_message = msg
        logger.error(msg)

    except TrafoExecutionComponentImportsLoadingError as err:
        msg = f"Could not load some component import components:\n{str(err)}"
        scheduled_job_info.state = ScheduledJobState.INVOCATION_ERROR
        scheduled_job_info.error_message = msg
        logger.error(msg)

    except TrafoExecutionComponentAdapterComponentsNotFound as err:
        msg = (
            "Could not find component revision for component adapter wirings or"
            " could not validate them as suitable component sources/sinks when"
            f" executing {exec_by_id.id}:\n{str(err)} with wiring\n{exec_by_id.wiring}."
            f" Exception was:\n{str(err)}"
        )
        scheduled_job_info.state = ScheduledJobState.INVOCATION_ERROR
        scheduled_job_info.error_message = msg
        logger.error(msg)

    except TrafoExecutionRuntimeHttpStatusError as err:
        # actually 4xx or 5xx
        msg = (
            f"Https status error during execution of transformation {exec_by_id.id} in external"
            f" runtime service:\n{str(err)}"
        )
        scheduled_job_info.state = ScheduledJobState.INVOCATION_ERROR
        scheduled_job_info.error_message = msg
        logger.error(msg)

    except TrafoExecutionRuntimeConnectionError as err:
        msg = f"Could not connect to runtime to execute transformation {exec_by_id.id}:\n{str(err)}"
        scheduled_job_info.state = ScheduledJobState.INVOCATION_ERROR
        scheduled_job_info.error_message = msg
        logger.error(msg)

    except TrafoExecutionResultValidationError as err:
        msg = f"Could not validate execution result for transformation {exec_by_id.id}:\n{str(err)}"
        scheduled_job_info.state = ScheduledJobState.INVOCATION_ERROR
        scheduled_job_info.error_message = msg
        logger.error(msg)

    except Exception as err:  # noqa: BLE001
        msg = (
            f"ERROR: Generally uncaught exception during execution of "
            f"transformation {exec_by_id.id}:\n{str(err)}"
        )
        scheduled_job_info.state = ScheduledJobState.INVOCATION_ERROR
        scheduled_job_info.error_message = msg
        logger.error(msg)

    if scheduled_job_info.state != ScheduledJobState.INVOCATION_ERROR:
        if exec_result.error is None:
            scheduled_job_info.state = ScheduledJobState.SUCCESS
        else:
            scheduled_job_info.state = ScheduledJobState.EXECUTION_ERROR

        scheduled_job_info.exec_result = exec_result

    logger.info(
        "Scheduled job %s with name %s with trafo exec job id %s execution result: %s",
        job_id,
        name,
        exec_job_id,
        str(scheduled_job_info.state),
        extra={
            "scheduled_job_information": scheduled_job_info.model_dump(mode="json"),
        },
    )


async def sync_job() -> None:
    """Sync schedule jobs from backend db

    This syncs the jobs stored / managed by the backend in the database
    with the apscheduler instance.

    This itself is an always-running job of the scheduler instance.

    Jobs removed from the scheduler instance if they are not present in the database
    anymore or if they are inactive.

    Jobs are added to the scheduler instance if they are present in the database, do
    not already exist and are active.

    Existing jobs where the underlying schedule entity changed in the database are
    rescheduled by removing and adding them to the scheduler instance.

    To detect changes, the schedule infos are stored in-memory in get_global_schedule_infos
    and are compared to the corresponding schedule entities from the database.
    """
    scheduler = get_global_scheduler()
    logger.debug("Syncing scheduled jobs")
    all_schedules = get_multiple_schedules()

    global_schedule_infos = get_global_schedule_infos()

    scheduled_job_ids = {job.id for job in scheduler.get_jobs()}
    db_schedules_by_job_id = {f"job_{str(schedule.id)}": schedule for schedule in all_schedules}

    # Remove jobs that are no longer in the database or are inactive
    for job_id in scheduled_job_ids:
        if job_id.startswith("job_"):
            if job_id not in db_schedules_by_job_id:
                scheduler.remove_job(job_id)
                logger.info(
                    "Removed job %s from scheduler because it does not exist anymore", job_id
                )
            elif not db_schedules_by_job_id[job_id].active:
                scheduler.remove_job(job_id)
                logger.info("Removed job %s from scheduler because it is inactive", job_id)

    # Add or update jobs from database
    for schedule in (s for s in all_schedules if s.active):
        job_id_str = f"job_{str(schedule.id)}"

        existing_job = scheduler.get_job(job_id_str)  # None if not found
        existing_job_schedule = global_schedule_infos.get(job_id_str, None)

        if (
            existing_job_schedule is None
            or existing_job is None
            or existing_job_schedule != schedule  # changed
        ):
            if existing_job is not None:
                logger.debug("Remove existing schedule job %s", job_id_str)
                scheduler.remove_job(job_id_str)
                global_schedule_infos.pop(job_id_str, None)

            try:
                trigger_from_db = CronTrigger.from_crontab(
                    schedule.cron_expression, timezone=datetime.UTC
                )
            except ValueError as e:
                logger.error(
                    "Job %s with name %s has invalid cron expression and cannot be scheduled!: %s",
                    job_id_str,
                    schedule.name,
                    str(e),
                )
                trigger_from_db = None

            if trigger_from_db is not None:
                global_schedule_infos[job_id_str] = schedule

                scheduler.add_job(
                    execute_scheduled_transformation,
                    args=[job_id_str, schedule.name],
                    trigger=trigger_from_db,
                    id=job_id_str,
                    name=schedule.name,
                )
                logger.info(
                    "Job %s activated, changed or synced first time, (re)scheduling with name %s",
                    job_id_str,
                    schedule.name,
                )


async def start_scheduler() -> None:
    """Initialize and start scheduler"""
    scheduler = get_global_scheduler()
    sync_interval_seconds = get_config().scheduling_sync_interval_seconds
    scheduler.add_job(sync_job, trigger="interval", seconds=sync_interval_seconds)
    scheduler.start()
    logger.info("Scheduler started with %s seconds db sync interval.", sync_interval_seconds)


def run_scheduler() -> None:
    """Run the async scheduler in its own event loop"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Run the scheduler startup as a coroutine
    loop.run_until_complete(start_scheduler())

    # Keep the loop running
    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        get_global_scheduler().shutdown()


def start_scheduling(in_memory_db: bool) -> None:
    is_backend_service = get_config().is_backend_service
    scheduling_requested = get_config().scheduling_active

    if scheduling_requested and not is_backend_service:
        logger.warning(
            "Active Scheduling is only allowed in a backend service. Not activating scheduling!"
        )
        return

    if not scheduling_requested:
        logger.info("Scheduling inactive.")
        return

    if in_memory_db:
        logger.warning(
            "Scheduling needs a proper persistent database."
            " In-memory database detected. Not activating scheduling!"
        )
        return

    logger.info("Starting scheduling in separate thread.")

    # Start scheduler in a separate daemon thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    # Give scheduler time to start
    time.sleep(1)
