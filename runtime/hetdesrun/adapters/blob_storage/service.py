from logging import getLogger
from typing import List

from hetdesrun.adapters.blob_storage.models import BucketName, IdString

logger = getLogger(__name__)


def get_buckets() -> List[BucketName]:
    logger.info("get buckets")
    return [BucketName("i-i"), BucketName("i-ii"), BucketName("i-iii")]


def get_object_key_strings_in_bucket(bucket_name: BucketName) -> List[IdString]:
    if bucket_name == "i-i":
        return [
            IdString("A_2022Y01M02D14h23m18s"),
            IdString("A_2022Y01M02D14h57m31s"),
            IdString("B_2022Y01M02D14h25m56s"),
            IdString("D_2022Y03M08D17h23m18s"),
            IdString("D_2022Y04M02D13h28m29s"),
        ]
    if bucket_name == "i-ii":
        return [IdString("E_2022Y01M02D14h23m18s")]
    if bucket_name == "i-iii":
        return [IdString("H_2022Y12M05D14h41m55s")]
    return []
