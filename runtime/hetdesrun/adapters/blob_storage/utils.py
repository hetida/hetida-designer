from logging import getLogger
from typing import List

from hetdesrun.adapters.blob_storage.models import (
    BlobStorageStructureSource,
    ObjectKey,
    get_adapter_structure,
)
from hetdesrun.adapters.blob_storage.service import get_object_key_strings_in_bucket

logger = getLogger(__name__)


def create_sources() -> List[BlobStorageStructureSource]:
    thing_nodes = get_adapter_structure().thing_nodes
    buckets = get_adapter_structure().structure_buckets
    source_list: List[BlobStorageStructureSource] = []
    for bucket in buckets:
        object_key_strings = get_object_key_strings_in_bucket(bucket.name)
        for object_key_string in object_key_strings:
            object_key = ObjectKey.from_string(object_key_string)

            # ignore objects that do not match the config hierarchy
            thing_node_id = object_key.to_thing_node_id(bucket)
            if len([tn for tn in thing_nodes if tn.id == thing_node_id]) == 0:
                continue
            source = BlobStorageStructureSource.from_structure_bucket_and_object_key(
                bucket=bucket, object_key=object_key
            )
            source_list.append(source)
            logger.debug("Created source:\n%s", source)

    return source_list
