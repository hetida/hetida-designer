from logging import getLogger
from typing import Final

logger = getLogger(__name__)

try:
    with open("VERSION", "r", encoding="utf8") as version_file:
        VERSION = version_file.read().strip()
except FileNotFoundError:
    VERSION = "dev snapshot"

BUCKET_NAME_DIR_SEPARATOR: Final = "-"
OBJECT_KEY_DIR_SEPARATOR: Final = "/"
IDENTIFIER_SEPARATOR: Final = "_"
LEAF_NAME_SEPARATOR: Final = " - "
TIME_STRING_FORMAT: Final = "%YY%mM%dD%Hh%Mm%Ss"
SINK_ID_ENDING: Final = "next"
SINK_NAME_ENDING: Final = "Next Object"
