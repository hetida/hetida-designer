"""Module for development/debugging execution of the Web Service

In production the service will probably be executed using asgi in
a proper webserving environment in a container.

This file can be used for development/testing/debugging of the
webservice using uvicorn as development web server.

Usage: Call with activated virtual environment via
    python main.py
from project directory.
"""

import os

# pylint: disable=wrong-import-order
import logging

if __name__ == "__main__":
    if os.environ.get("HD_RUNTIME_ENVIRONMENT_FILE", None) is None:
        # if this script is called directly, default to local dev setup.
        os.environ["HD_RUNTIME_ENVIRONMENT_FILE"] = "local_dev.env"


from hetdesrun import configure_logging

logger = logging.getLogger(__name__)
configure_logging(logger)

# must be after logging config:
from hetdesrun.webservice import get_app
from hetdesrun.webservice.config import get_config

app = get_app()


def detect_in_memory_db() -> bool:
    from hetdesrun.persistence import get_db_engine

    engine = get_db_engine()

    backend_name = engine.url.get_backend_name()

    # driver_name = engine.url.get_driver_name()  # pysqlite
    database = engine.url.database  # ":memory:"

    if backend_name.lower() == "sqlite" and (
        (database is None) or database.lower() in (":memory:",)
    ):
        return True

    return False


def run_migrations(
    alembic_dir: str = "./alembic",
    connection_url=get_config().sqlalchemy_connection_string,
) -> None:
    """Runs alembic migrations from within Python code

    Should only be used for local development server. Not recommended
    for multi-process/thread production servers.

    Note: The docker container runs migrations via prestart.sh script in the
    production setup.
    """

    from hetdesrun import migrations_invoked_from_py

    migrations_invoked_from_py = True

    from alembic.config import Config
    from alembic import command
    from pydantic import SecretStr
    import hetdesrun.persistence.dbmodels

    from hetdesrun.persistence import get_db_engine

    engine = get_db_engine()

    logger.info("Using DB engine driver: %s", str(engine.url.drivername))

    if isinstance(connection_url, SecretStr):
        connection_url_to_use = connection_url.get_secret_value()
    else:
        connection_url_to_use = connection_url

    logger.info("Running DB migrations in %s", alembic_dir)
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", alembic_dir)
    # alembic_cfg.set_main_option("sqlalchemy.url", connection_url_to_use)
    # alembic_cfg.set_section_option("logger_root", "level", "DEBUG")
    # alembic_cfg.set_section_option("logger_alembic", "level", "DEBUG")
    # alembic_cfg.set_section_option("logger_sqlalchemy", "level", "DEBUG")
    command.upgrade(alembic_cfg, "head")
    logger.info("Finished running migrations.")


in_memory_db = detect_in_memory_db()

if in_memory_db:
    logger.info(
        "Detected in-memory db usage: Running migrations during importing of main.py."
    )
    run_migrations()

if __name__ == "__main__":

    if not in_memory_db:
        logger.info(
            "Running migrations from main.py since main.py was invoked directly."
        )
        run_migrations()

    import os
    import uvicorn

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 8000))
    logger.info("Start app as host %s with port %s", str(host), str(port))
    uvicorn.run(
        "hetdesrun.webservice.application:app",
        debug=True,
        reload=True,
        host=host,
        port=port,
    )
