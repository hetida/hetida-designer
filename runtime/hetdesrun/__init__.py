import logging

import structlog
from structlog.types import Processor

import hetdesrun_config  # noqa: F401
from hetdesrun.runtime import internal_runtime_execution_logger
from hetdesrun.runtime import runtime_execution_logger as logger
from hetdesrun.runtime import runtime_logger as job_logger
from hetdesrun.runtime.logging import (
    ComponentCodeLogHandler,
    CustomAttributeProcessor,
    FieldRenamer,
    MinimallyMoreCapableJsonEncoder,
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


# Processors that should run on all stdlib logging entries
SHARED_PROCESSORS: list[Processor] = [
    structlog.processors.TimeStamper(fmt="iso", utc=True),  # timestamp hinzu
    structlog.stdlib.add_log_level,  # log level
    structlog.stdlib.add_logger_name,  # logger name
    structlog.processors.CallsiteParameterAdder(
        {
            structlog.processors.CallsiteParameter.FILENAME,
            structlog.processors.CallsiteParameter.FUNC_NAME,
            structlog.processors.CallsiteParameter.LINENO,
        }
    ),
    structlog.processors.format_exc_info,  # for exception propagation
    CustomAttributeProcessor(),  # to get added fields from logging.filters in records
    structlog.stdlib.ProcessorFormatter.remove_processors_meta,  # removes unneccesary information
    FieldRenamer(),  # renames fields
    structlog.processors.StackInfoRenderer(),
]

# Configure structlog
structlog.configure(
    processors=SHARED_PROCESSORS
    + [
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)


def get_formatter(
    processors: list[Processor] | None = None,
) -> structlog.stdlib.ProcessorFormatter:
    """Creates and returns a structlog formatter that bridges stdlib logging and structlog"""
    return structlog.stdlib.ProcessorFormatter(
        # Run only on entries foreign to structlog, stdlib logging in our case
        foreign_pre_chain=SHARED_PROCESSORS,
        # Run on all entries
        processors=(
            [
                structlog.processors.JSONRenderer(
                    default=MinimallyMoreCapableJsonEncoder().default
                ),
            ]
            + (processors or [])  # type: ignore
        ),
    )


def configure_logging(
    the_logger: logging.Logger,
    log_execution_context: bool = False,
    log_job_id_context: bool = False,
    additional_processors: list[Processor] | None = None,
) -> None:
    """Configure logging

    Arguments:
        the_logger {Python logger} -- any logger

    Keyword Arguments:
        log_execution_context {bool} -- Whether runtime execution context should
            be made available and logged (default: {False})
        log_job_id_context {bool} -- Whether job ID should
            be made available and logged (default: {False})
        additional_processors {list[Processor]} -- List of processors to be added to the formatter
            in addition to the default processors in get_formatter (default: {None})

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
    formatter = get_formatter(additional_processors)
    logging_handler.setFormatter(formatter)
    the_logger.addHandler(logging_handler)


main_logger = logging.getLogger(__name__)
configure_logging(main_logger)

configure_logging(logger, log_execution_context=True)

configure_logging(internal_runtime_execution_logger, log_execution_context=True)

# Add component code handler to gather component code logs
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


def setup_third_party_loggers(
    logger_names: list[str],
    configure: bool = False,
    log_job_id_context: bool = False,
) -> None:
    """Strip handlers from third-party loggers and optionally configure them."""
    for logger_name in logger_names:
        third_party_logger = logging.getLogger(logger_name)
        third_party_logger.handlers.clear()
        if configure:
            configure_logging(third_party_logger, log_job_id_context=log_job_id_context)


if get_config().log_httpx:
    setup_third_party_loggers(["httpx", "httpcore"], configure=True, log_job_id_context=True)

# Always strip handlers from uvicorn loggers as they are enabled by default
setup_third_party_loggers(
    ["uvicorn", "uvicorn.access"], configure=get_config().log_uvicorn, log_job_id_context=True
)

main_logger.info("Logging setup complete.", extra={"version": VERSION})

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
