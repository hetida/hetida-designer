import logging

import hetdesrun_config  # noqa: F401
from hetdesrun.runtime import internal_runtime_execution_logger
from hetdesrun.runtime import runtime_execution_logger as logger
from hetdesrun.runtime import runtime_logger as job_logger
from hetdesrun.runtime.logging import (
    ComponentCodeLogHandler,
    execution_context_filter,
    job_id_context_filter,
)
from hetdesrun.webservice.config import get_config

migrations_invoked_from_py = False

try:
    with open("VERSION", encoding="utf8") as version_file:
        VERSION = version_file.read().strip()
except FileNotFoundError:
    VERSION = "dev snapshot"


def get_formatter(
    log_execution_context: bool = False, log_job_id_context: bool = False
) -> logging.Formatter:
    return logging.Formatter(
        "%(asctime)s %(process)d %(levelname)s: %(message)s "
        "[in %(pathname)s:%(lineno)d"
        + (
            ", job_id=%(currently_executed_job_id)s"
            if log_job_id_context or log_execution_context
            else ""
        )
        + (
            (
                ",\n    tr type: %(currently_executed_transformation_type)s"
                ", tr id: %(currently_executed_transformation_id)s"
                ", tr name: %(currently_executed_transformation_name)s"
                ", tr tag: %(currently_executed_transformation_tag)s"
                ",\n    op id(s): %(currently_executed_operator_hierarchical_id)s"
                ",\n    op name(s): %(currently_executed_operator_hierarchical_name)s"
                "\n"
            )
            if log_execution_context
            else ""
        )
        + "]"
    )


def configure_logging(
    the_logger: logging.Logger,
    log_execution_context: bool = False,
    log_job_id_context: bool = False,
) -> None:
    """Configure logging

    Arguments:
        the_logger {Python logger} -- any logger

    Keyword Arguments:
        log_execution_context {bool} -- whether runtime execution context should
            be made available and logged (default: {False})

    If log_execution_context is True a LoggingFilter will be attached to the
    LogHandler. Attaching to the handler (instead of the logger) guarantees that
    the filter will be applied even when descendant loggers are used which don't have
    handlers on their own (confer https://docs.python.org/3/_images/logging_flow.png)

    This filter actually does no filtering but augments the LogRecords with
    execution context information (id of component instance and component uuid).
    A filter is used here for context provision because it can be attached to
    a handler (in contrast to a LoggingAdapter). Attaching the filter to custom
    LoggingHandlers allows to send this information to external services.

    Additionally the formatter is set up to log this context information.
    """
    the_logger.setLevel(get_config().log_level.value)
    logging_handler = logging.StreamHandler()  # use sys.stderr by default
    # sys.stderr will be propagated by mod_wsgi to Apache error log for webservice
    if log_job_id_context:
        logging_handler.addFilter(job_id_context_filter)
    if log_execution_context:
        logging_handler.addFilter(execution_context_filter)
    formatter = get_formatter(log_execution_context, log_job_id_context)
    logging_handler.setFormatter(formatter)
    the_logger.addHandler(logging_handler)


main_logger = logging.getLogger(__name__)
configure_logging(main_logger)

configure_logging(logger, log_execution_context=True)

configure_logging(internal_runtime_execution_logger, log_execution_context=True)

# add component code handler to gather component code logs
component_code_handler = ComponentCodeLogHandler()
component_code_handler.addFilter(job_id_context_filter)
component_code_handler.addFilter(execution_context_filter)
logger.addHandler(ComponentCodeLogHandler())

logger.setLevel(
    get_config().user_component_code_log_level.value  # type: ignore
    if get_config().user_component_code_log_level is not None
    else get_config().log_level.value
)

configure_logging(job_logger, log_job_id_context=True)

if get_config().log_httpx:
    httpx_logger = logging.getLogger("httpx")
    configure_logging(httpx_logger, log_job_id_context=True)

    httpcore_logger = logging.getLogger("httpcore")
    configure_logging(httpcore_logger, log_job_id_context=True)

main_logger.info("Logging setup complete.")

# preload frequently used ds libraries in order to avoid overhead
# during first call in a worker process for many workflows/components
# and mitigate distorting effect of imports for performance measurements
if get_config().is_runtime_service:
    import numpy as np  # noqa: F401
    import pandas as pd  # noqa: F401
    import plotly.express as px  # noqa: F401
    import plotly.graph_objects as go  # noqa: F401
    import plotly.io as pio  # noqa: F401
    import scipy  # noqa: F401
    from plotly.graph_objects import Figure  # noqa: F401
