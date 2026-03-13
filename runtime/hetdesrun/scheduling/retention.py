import datetime
import logging

from hetdesrun.persistence.dbservice.schedule import delete_old_schedule_executions
from hetdesrun.webservice.config import get_config

logger = logging.getLogger(__name__)


async def executions_retention_job() -> None:
    """Deletes schedule executions older than configured retention"""
    older_than = datetime.datetime.now(datetime.UTC) - get_config().scheduling_executions_retention
    logger.info("Deleting schedule executions older than %s", older_than)
    delete_old_schedule_executions(older_than)
