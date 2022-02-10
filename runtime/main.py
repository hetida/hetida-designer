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

from hetdesrun.webservice.application import app
from hetdesrun.webservice.config import runtime_config


logger = logging.getLogger(__name__)
configure_logging(logger)


def init_db():
    if runtime_config.is_backend_service and runtime_config.ensure_db_schema:
        logger.info("Checking DB status")
        from sqlalchemy_utils import create_database
        from hetdesrun.persistence.dbmodels import Base
        from hetdesrun.persistence import get_db_engine
        from sqlalchemy_utils.functions import database_exists

        engine = get_db_engine()

        logger.info("Using DB engine driver: %s", str(engine.url.drivername))

        if not database_exists(engine.url):
            logger.info("Creating DB database")
            create_database(get_db_engine().url)

            Base.metadata.drop_all(get_db_engine())
        else:
            logger.info("DB database already exists. Not creating.")
        logger.info("Creating Schema (if it does not exist)")
        Base.metadata.create_all(get_db_engine(), checkfirst=True)


init_db()  # init db database and schema if not present and if running as backend

if __name__ == "__main__":

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
