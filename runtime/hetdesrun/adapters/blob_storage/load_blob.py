import logging
from typing import Any

logger = logging.getLogger(__name__)


def load_blob_from_storage(source_id: str) -> Any:
    logger.info("Load blob from storage for source_id %s", source_id)
    return {source_id}
