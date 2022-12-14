from logging import getLogger
from typing import List

from hetdesrun.adapters.blob_storage.models import BucketName, IdString

logger = getLogger(__name__)


def get_object_key_strings_in_bucket(bucket_name: BucketName) -> List[IdString]:
    if bucket_name == "i-i":
        return [
            IdString("A_2022-01-02T14:23:18+00:00"),
            IdString("A_2022-01-02T14:57:31+00:00"),
            IdString("B_2022-01-02T14:25:56+00:00"),
            IdString("D_2022-03-08T17:23:18+00:00"),
            IdString("D_2022-04-02T13:28:29+00:00"),
        ]
    if bucket_name == "i-ii":
        return [IdString("E_2022-01-02T14:23:18+00:00")]
    if bucket_name == "i-iii":
        return [IdString("H_2022-12-05T14:41:55+00:00")]
    return []
