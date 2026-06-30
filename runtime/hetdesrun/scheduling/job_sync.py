import datetime
import logging

from apscheduler.triggers.cron import CronTrigger

from hetdesrun.persistence.dbservice.schedule import get_multiple_schedules
from hetdesrun.scheduling.execution import execute_scheduled_transformation
from hetdesrun.scheduling.scheduler import get_global_schedule_infos, get_global_scheduler

logger = logging.getLogger(__name__)


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
            except ValueError as e:  # pragma: no cover
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
