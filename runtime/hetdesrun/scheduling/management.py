import asyncio
import logging
import threading
import time

import httpx

from hetdesrun.backend.runtime_http_client import runtime_http_client
from hetdesrun.scheduling.job_sync import sync_job
from hetdesrun.scheduling.retention import executions_retention_job
from hetdesrun.scheduling.scheduler import get_global_scheduler
from hetdesrun.webservice.config import get_config

logger = logging.getLogger(__name__)


async def start_scheduler() -> None:  # pragma: no cover
    """Initialize and start scheduler"""
    scheduler = get_global_scheduler()

    # initialize runtime http client

    scheduling_runtime_http_client = httpx.AsyncClient(
        verify=get_config().hd_runtime_verify_certs,
        timeout=get_config().external_request_timeout,
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
    )
    runtime_http_client.set(scheduling_runtime_http_client)

    # sync job
    sync_interval_seconds = get_config().scheduling_sync_interval_seconds
    scheduler.add_job(sync_job, trigger="interval", seconds=sync_interval_seconds)

    # retention job
    executions_retention_seconds = (
        get_config().scheduling_executions_retention_deletion_job_interval_seconds
    )
    scheduler.add_job(
        executions_retention_job, trigger="interval", seconds=executions_retention_seconds
    )

    # start scheduler
    scheduler.start()
    logger.info("Scheduler started with %s seconds db sync interval.", sync_interval_seconds)


def run_scheduler() -> None:  # pragma: no cover
    """Run the async scheduler in its own event loop"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Run the scheduler startup as a coroutine
    loop.run_until_complete(start_scheduler())

    # Keep the loop running
    try:
        loop.run_forever()
    except KeyboardInterrupt, SystemExit:
        pass
    finally:
        get_global_scheduler().shutdown()


def start_scheduling(in_memory_db: bool) -> None:  # pragma: no cover
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
