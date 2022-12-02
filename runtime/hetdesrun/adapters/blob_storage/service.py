from logging import getLogger
from typing import List

from hetdesrun.adapters.blob_storage.models import BucketName, IdString

logger = getLogger(__name__)


def get_buckets() -> List[BucketName]:
    logger.info("get buckets")
    return [BucketName("I-i"), BucketName("I-ii"), BucketName("I-iii")]


def get_object_key_strings_in_bucket(bucket_name: BucketName) -> List[IdString]:
    if bucket_name == "I-i":
        return [
            IdString("A-2022Y01M02D14h23m18s"),
            IdString("A-2022Y01M02D14h57m31s"),
            IdString("B-2022Y01M02D14h25m56s"),
            IdString("D-2022Y03M08D17h23m18s"),
            IdString("D-2022Y04M02D13h28m29s"),
        ]
    if bucket_name == "I-ii":
        return [IdString("E-2022Y01M02D14h23m18s")]
    return []
