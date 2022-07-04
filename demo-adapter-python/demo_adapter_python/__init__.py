import logging

from demo_adapter_python.config import demo_adapter_config

try:
    with open("VERSION", "r", encoding="utf8") as version_file:
        VERSION = version_file.read().strip()
except FileNotFoundError:
    VERSION = "dev snapshot"


def configure_logging(the_logger: logging.Logger) -> None:
    """Setup Logging"""
    the_logger.setLevel(demo_adapter_config.log_level.value)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s " "[in %(pathname)s:%(lineno)d]"
    )
    logging_handler = logging.StreamHandler()
    logging_handler.setFormatter(formatter)
    the_logger.addHandler(logging_handler)


main_logger = logging.getLogger(__name__)
configure_logging(main_logger)

main_logger.info("Logging setup complete.")
