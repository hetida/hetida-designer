import logging
from hetdesrun.webservice.config import runtime_config
from hetdesrun.runtime.logging import execution_context_filter
from hetdesrun.runtime import runtime_component_logger as logger

import hetdesrun_config

migrations_invoked_from_py = False

try:
    with open("VERSION", "r", encoding="utf8") as version_file:
        VERSION = version_file.read().strip()
except FileNotFoundError:
    VERSION = "dev snapshot"


def configure_logging(
    the_logger: logging.Logger, log_execution_context: bool = False
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
    the_logger.setLevel(runtime_config.log_level.value)
    logging_handler = logging.StreamHandler()  # use sys.stderr by default
    # sys.stderr will be propagated by mod_wsgi to Apache error log for webservice
    if log_execution_context:
        logging_handler.addFilter(execution_context_filter)
    formatter = logging.Formatter(
        "%(asctime)s %(process)d %(levelname)s: %(message)s "
        "[in %(pathname)s:%(lineno)d"
        + (
            (
                ", component instance: %(currently_executed_instance_id)s"
                ", component id: %(currently_executed_component_id)s"
                ", component node name: %(currently_executed_component_node_name)s"
                ", job id: %(job_id)s"
                "]"
            )
            if log_execution_context
            else "]"
        )
    )
    logging_handler.setFormatter(formatter)
    the_logger.addHandler(logging_handler)


main_logger = logging.getLogger(__name__)
configure_logging(main_logger)

main_logger.info("Logging setup complete.")

configure_logging(logger, log_execution_context=True)
