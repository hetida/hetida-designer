import logging
from typing import Any

logger = logging.getLogger(__name__)


def write_blob_to_storage(blob: Any, sink_id: str) -> None:
    logger.info("Write blob %s to storage for sink_id %s", str(blob), sink_id)
