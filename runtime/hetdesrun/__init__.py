import logging

import hetdesrun_config  # noqa: F401
from hetdesrun.runtime import runtime_execution_logger as logger
from hetdesrun.runtime import runtime_logger as job_logger
from hetdesrun.runtime.logging import execution_context_filter, job_id_context_filter
from hetdesrun.webservice.config import get_config

migrations_invoked_from_py = False

try:
    with open("VERSION", encoding="utf8") as version_file:
        VERSION = version_file.read().strip()
except FileNotFoundError:
    VERSION = "dev snapshot"


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
    formatter = logging.Formatter(
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
    logging_handler.setFormatter(formatter)
    the_logger.addHandler(logging_handler)


main_logger = logging.getLogger(__name__)
configure_logging(main_logger)

main_logger.info("Logging setup complete.")

configure_logging(logger, log_execution_context=True)
configure_logging(job_logger, log_job_id_context=True)
