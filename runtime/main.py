"""Module for development/debugging execution of the Web Service

In production the service will probably be executed using asgi in
a proper webserving environment in a container.

This file can be used for development/testing/debugging of the
webservice using uvicorn as development web server.

Usage: Call with activated virtual environment via
    python main.py
from project directory.
"""

# pylint: disable=wrong-import-order
import logging
from hetdesrun import configure_logging

from hetdesrun.service.webservice import app


logger = logging.getLogger(__name__)
configure_logging(logger)

if __name__ == "__main__":

    import os
    import uvicorn

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 8000))
    logger.info("Start app as host %s with port %s", str(host), str(port))
    uvicorn.run(
        "hetdesrun.service.webservice:app",
        debug=True,
        reload=True,
        host=host,
        port=port,
    )
