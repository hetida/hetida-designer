from logging import getLogger

from hetdesrun.adapters.blob_storage.utils import setup_adapter

logger = getLogger(__name__)

try:
    with open("VERSION", "r", encoding="utf8") as version_file:
        VERSION = version_file.read().strip()
except FileNotFoundError:
    VERSION = "dev snapshot"


tns, srcs, snks = setup_adapter()
logger.info("Setup of Blob Storage Adapter complete!")
