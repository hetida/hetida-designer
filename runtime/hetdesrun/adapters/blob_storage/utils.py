from logging import getLogger
from typing import List

from hetdesrun.adapters.blob_storage.exceptions import MissingHierarchyError
from hetdesrun.adapters.blob_storage.models import (
    BlobStorageStructureSource,
    ObjectKey,
    get_adapter_structure,
)
from hetdesrun.adapters.blob_storage.service import get_object_key_strings_in_bucket
from hetdesrun.adapters.exceptions import AdapterConnectionError

logger = getLogger(__name__)


def create_sources() -> List[BlobStorageStructureSource]:
    try:
        thing_nodes = get_adapter_structure().thing_nodes
        buckets = get_adapter_structure().structure_buckets
    except MissingHierarchyError as error:
        raise error
    source_list: List[BlobStorageStructureSource] = []
    for bucket in buckets:
        try:
            object_key_strings = get_object_key_strings_in_bucket(bucket.name)
        except AdapterConnectionError as error:
            raise error
        for object_key_string in object_key_strings:
            try:
                object_key = ObjectKey.from_string(object_key_string)
            except ValueError:
                # ignore objects with keys that do not match the expected name scheme
                continue

            # ignore objects that do not match the configured hierarchy
            thing_node_id = object_key.to_thing_node_id(bucket)
            if len([tn for tn in thing_nodes if tn.id == thing_node_id]) == 0:
                continue
            source = BlobStorageStructureSource.from_structure_bucket_and_object_key(
                bucket=bucket, object_key=object_key
            )
            source_list.append(source)
            logger.debug("Created source:\n%s", source)

    return source_list
