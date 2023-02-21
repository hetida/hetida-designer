from logging import getLogger
from typing import Final

logger = getLogger(__name__)

try:
    with open("VERSION", encoding="utf8") as version_file:
        VERSION = version_file.read().strip()
except FileNotFoundError:
    VERSION = "dev snapshot"

BUCKET_NAME_DIR_SEPARATOR: Final = "-"
OBJECT_KEY_DIR_SEPARATOR: Final = "/"
IDENTIFIER_SEPARATOR: Final = "_"
HIERARCHY_END_NODE_NAME_SEPARATOR: Final = " - "
GENERIC_SINK_ID_SUFFIX: Final = "generic_sink"
GENERIC_SINK_NAME_SUFFIX: Final = "Next Object"
