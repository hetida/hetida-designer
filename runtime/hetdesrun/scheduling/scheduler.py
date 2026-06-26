import functools
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from hetdesrun.persistence.models.schedule import Schedule

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
