import logging
from typing import Any

logger = logging.getLogger(__name__)


def load_blob_from_storage(source_id: str) -> Any:
    logger.info("Write blob to storage for source_id %s", source_id)
    return {"test": source_id}
