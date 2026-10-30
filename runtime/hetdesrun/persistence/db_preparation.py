"""Preparation of the db at backend start

The backend migrates the db, deploys the base trafos, prepopulates the virtual structure
adapter and runs the autoimport before the web server starts, see main.py and
docs/deployment_operation/database_configuration.md.
"""

import logging
import os
import sys
import time

from alembic.config import Config

from alembic import command
from hetdesrun.adapters.virtual_structure_adapter.config import get_vst_adapter_config
from hetdesrun.adapters.virtual_structure_adapter.structure_prepopulation import (
    prepopulate_structure,
)
from hetdesrun.exportimport.importing import (
    autodeploy_base_transformations,
    autoimport_at_backend_start,
)
from hetdesrun.persistence.db_engine_and_session import db_url_for_logging, is_in_memory_db
from hetdesrun.webservice.config import get_config

logger = logging.getLogger(__name__)


def run_migrations(
    alembic_dir: str = "./alembic", max_attempts: int = 10, retry_wait_seconds: float = 5
) -> None:
    """Migrate the db schema to the revision HD_TARGET_ALEMBIC_REVISION

    Retries, e.g. if the db is not available yet.
    """
    target_revision = get_config().target_alembic_revision or "head"
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", alembic_dir)

    for attempt in range(1, max_attempts + 1):
        logger.info(
            "Running db migrations to revision %s (attempt %i of %i)",
            target_revision,
            attempt,
            max_attempts,
        )
        try:
            command.upgrade(alembic_cfg, target_revision)
        except Exception:
            if attempt == max_attempts:
                logger.error("Db migrations finally failed after %i attempts.", max_attempts)
                raise
            logger.warning(
                "Db migrations failed on attempt %i. Retrying in %s seconds.",
                attempt,
                retry_wait_seconds,
                exc_info=True,
            )
            time.sleep(retry_wait_seconds)
        else:
            logger.info("Finished db migrations.")
            return


def prepare_db() -> None:
    """Migrate the db, deploy the base trafos, prepopulate the vst adapter and run the autoimport"""
    run_migrations()
    autodeploy_base_transformations()

    if get_vst_adapter_config().prepopulate_virtual_structure_adapter_at_designer_startup:
        logger.info("Prepopulating the structure of the virtual structure adapter.")
        prepopulate_structure()

    autoimport_at_backend_start()


def exit_unless_in_memory_db_allowed(
    require_allowance: bool = True, gunicorn_mode: bool = False
) -> None:
    """Exit if the in-memory db cannot be used like this

    An in-memory db exists only in the process using it, so it requires a single web server
    process. In the docker image (require_allowance) it must additionally be allowed explicitly
    via HD_ALLOW_IN_MEMORY_DB, since all data stored in it is lost when the backend stops.
    """
    if require_allowance and not get_config().allow_in_memory_db:
        error = (
            "The configured database is an in-memory database. All components, workflows and"
            " further data stored in it are lost when the backend stops. Do you really want"
            " this? Otherwise check the database configuration, i.e. HD_DATABASE_URL or"
            " HD_DB_DRIVERNAME and HD_DB_DATABASE, also in the file set via"
            " HD_RUNTIME_ENVIRONMENT_FILE. If you really want an in-memory database, you must"
            " allow it explicitly by setting HD_ALLOW_IN_MEMORY_DB=true."
        )
    elif (web_concurrency := os.environ.get("WEB_CONCURRENCY", "")) not in ("", "1"):
        error = (
            "An in-memory database requires a single web server process, since each process"
            " would have its own database. Unset WEB_CONCURRENCY or set it to 1"
            f" (it is {web_concurrency})."
        )
    elif gunicorn_mode:
        error = (
            "An in-memory database is not supported in the deprecated gunicorn mode."
            " Use the pure uvicorn mode, i.e. unset HETIDA_DESIGNER_PURE_UVICORN"
            " or set it to true."
        )
    else:
        if require_allowance:
            logger.warning(
                "Using an in-memory database as allowed via HD_ALLOW_IN_MEMORY_DB. All data"
                " stored in it is lost when the backend stops. Scheduling is not available."
            )
        return

    logger.error(error)
    sys.exit(1)


def prepare_db_before_gunicorn() -> None:
    """Prepare the db in the deprecated gunicorn mode

    Used by start.sh, since gunicorn does not run main.py as main module.
    """
    if not get_config().is_backend_service:
        return

    logger.info("Backend uses db %s", db_url_for_logging())
    if is_in_memory_db():
        exit_unless_in_memory_db_allowed(gunicorn_mode=True)
    prepare_db()
