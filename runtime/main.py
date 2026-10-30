"""Module for development/debugging and actual execution of the Web Service

Usage: Call with activated virtual environment via
    python main.py
from project directory.

The docker image starts it via start.sh as
    python main.py --container
"""

import argparse
import asyncio
import datetime
import logging
import os
import signal
import sys

container_mode = False


def exit_on_signal(signum: int, _frame: object) -> None:
    os.write(2, f"Received signal {signum} before serving, exiting.\n".encode())
    sys.exit(128 + signum)


if __name__ == "__main__":
    # Stop on SIGTERM (e.g. docker stop) also while preparing the db, i.e. before the server
    # handles it. As PID 1 in a container this process otherwise ignores SIGTERM.
    signal.signal(signal.SIGTERM, exit_on_signal)

    parser = argparse.ArgumentParser(description="Start hetida designer backend and/or runtime.")
    parser.add_argument(
        "--container",
        action="store_true",
        help=(
            "Start as in the docker image via start.sh: local_dev.env is not used by default"
            " and an in-memory db must be allowed explicitly, see HD_ALLOW_IN_MEMORY_DB."
        ),
    )
    container_mode = parser.parse_args().container

    if (
        not container_mode
        and os.environ.get("HD_RUNTIME_ENVIRONMENT_FILE", None) is None
        and os.path.isfile("local_dev.env")
    ):
        # if this script is called directly, default to local dev setup.
        os.environ["HD_RUNTIME_ENVIRONMENT_FILE"] = "local_dev.env"


from hetdesrun import configure_logging
from hetdesrun.scheduling.management import start_scheduling

print(  # noqa: T201
    (
        f"[DIAG pid={os.getpid()}] main module base imports done."
        f"t={datetime.datetime.now(datetime.timezone.utc).isoformat()}"
    ),
    file=sys.stderr,
    flush=True,
)


logger = logging.getLogger(__name__)


configure_logging(logger)

print(  # noqa: T201
    (
        f"[DIAG pid={os.getpid()}] main module logging configured."
        f"t={datetime.datetime.now(datetime.timezone.utc).isoformat()}"
    ),
    file=sys.stderr,
    flush=True,
)


# must be after logging config:
from hetdesrun.webservice import get_app
from hetdesrun.webservice.config import get_config

app = get_app()

print(  # noqa: T201
    (
        f"[DIAG pid={os.getpid()}] main module further imports done and app object obtained."
        f"t={datetime.datetime.now(datetime.timezone.utc).isoformat()}"
    ),
    file=sys.stderr,
    flush=True,
)


def detect_in_memory_db() -> bool:
    if not get_config().is_backend_service:
        return False

    from hetdesrun.persistence.db_engine_and_session import is_in_memory_db

    return is_in_memory_db()


in_memory_db = detect_in_memory_db()
print(  # noqa: T201
    (
        f"[DIAG pid={os.getpid()}] in memory db: {in_memory_db}."
        f"t={datetime.datetime.now(datetime.timezone.utc).isoformat()}"
    ),
    file=sys.stderr,
    flush=True,
)
is_backend = get_config().is_backend_service

# from the config, i.e. also from the environment file
kafka_consumption_modus = get_config().hd_kafka_consumption_mode is not None
stream_mode_modus = get_config().hd_stream_mode is not None


# Each process serving the app has its own in-memory db. The server (uvicorn, gunicorn) imports
# this module as "main" in it, after the same process possibly ran this file already as
# "__mp_main__" (uvicorn worker / reload processes) or as "__main__" (python main.py).
# Preparing the db only on import as "main" prepares it exactly once per serving process.
if in_memory_db and __name__ not in {"__main__", "__mp_main__"}:
    from hetdesrun.persistence.db_preparation import prepare_db

    logger.info("Detected in-memory db usage: Preparing the db of this process.")
    prepare_db()


if __name__ == "__main__":
    if is_backend:
        from hetdesrun.persistence.db_engine_and_session import db_url_for_logging
        from hetdesrun.persistence.db_preparation import (
            exit_unless_in_memory_db_allowed,
            prepare_db,
        )

        logger.info("Backend uses db %s", db_url_for_logging())

        if not in_memory_db:
            # before the web server starts, see docs/deployment_operation/database_configuration.md
            prepare_db()
        else:
            exit_unless_in_memory_db_allowed(require_allowance=container_mode)
            if kafka_consumption_modus or stream_mode_modus:
                # no server imports this module
                logger.info("Detected in-memory db usage: Preparing the db of this process.")
                prepare_db()

    # as before: the server handles SIGTERM itself, consumption and stream mode do not
    signal.signal(signal.SIGTERM, signal.SIG_DFL)

    if kafka_consumption_modus:
        import asyncio

        from hetdesrun.adapters.kafka.consumption_mode import start_consumption_mode

        asyncio.run(start_consumption_mode())

    elif stream_mode_modus:
        import asyncio

        from hetdesrun.streaming import start_streaming_mode

        asyncio.run(start_streaming_mode())

    else:
        import os

        import uvicorn

        start_scheduling(in_memory_db)

        host = os.environ.get("HOST", "127.0.0.1")

        # DEVELOPMENT_MODE only activates uvicorn reload
        reload_mode = os.environ.get("DEVELOPMENT_MODE", "").lower() in {"true", "yes", "y", "1"}
        port = int(os.environ.get("PORT", "8000"))
        worker_healthcheck_timeout = int(os.environ.get("UVICORN_TIMEOUT_WORKER_HEALTHCHECK", "30"))

        # Keepalive must clearly exceed the idle expiry of clients reusing connections, like the
        # backend's httpx clients for the runtime (5 seconds). Otherwise an idle connection may be
        # closed just as a request arrives on it, which drops the request (httpx.ReadError at the
        # client).
        timeout_keep_alive = int(os.environ.get("UVICORN_TIMEOUT_KEEP_ALIVE", "65"))

        log_level = os.environ.get("UVICORN_LOG_LEVEL", "info")
        web_concurrency = os.environ.get("WEB_CONCURRENCY", "UNSET")
        logger.info(
            (
                "Start uvicorn app as host %s with port %s with uvicorn log level %s%s"
                " with web concurrency %s, worker healthcheck timeout %s"
                " and keep-alive timeout %s"
            ),
            str(host),
            str(port),
            log_level,
            " in reload/development mode" if reload_mode else "",
            web_concurrency,
            worker_healthcheck_timeout,
            timeout_keep_alive,
        )

        uvicorn.run(
            "main:app",
            log_level=log_level,
            reload=reload_mode,
            host=host,
            port=port,
            timeout_worker_healthcheck=worker_healthcheck_timeout,
            timeout_keep_alive=timeout_keep_alive,
        )
