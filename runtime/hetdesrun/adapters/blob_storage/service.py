from logging import getLogger
from typing import List

from hetdesrun.adapters.blob_storage.models import BucketName

logger = getLogger(__name__)


def get_buckets() -> List[BucketName]:
    logger.info("get buckets")
    return []


def get_blobs_in_bucket(bucket_id: str) -> List[str]:
    if bucket_id == "bucketA":
        return []
    if bucket_id == "bucketB":
        return []
    return []
