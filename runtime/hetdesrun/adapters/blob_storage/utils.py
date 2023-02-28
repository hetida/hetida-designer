from logging import getLogger

from hetdesrun.adapters.blob_storage import (
    IDENTIFIER_SEPARATOR,
    OBJECT_KEY_DIR_SEPARATOR,
)
from hetdesrun.adapters.blob_storage.exceptions import StructureObjectNotFound
from hetdesrun.adapters.blob_storage.models import (
    BlobStorageStructureSource,
    IdString,
    ObjectKey,
    StructureBucket,
    get_adapter_structure,
    get_bucket_name_and_object_key_prefix_from_id,
)
from hetdesrun.adapters.blob_storage.service import get_object_key_strings_in_bucket

logger = getLogger(__name__)


async def get_all_sources_from_buckets_and_object_keys() -> list[
    BlobStorageStructureSource
]:
    """Get sources from buckets and object keys.

    A MissingHierarchyError raised from get_adapter_structure or an AdapterConnectionError
    raised from get_object_key_strings_in_bucket may occur.
    """
    thing_nodes = get_adapter_structure().thing_nodes
    buckets = get_adapter_structure().structure_buckets
    source_list: list[BlobStorageStructureSource] = []
    for bucket in buckets:
        object_key_strings = await get_object_key_strings_in_bucket(bucket.name)
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


async def get_source_by_id_from_bucket_and_object_key(
    source_id: IdString,
) -> BlobStorageStructureSource:
    """Get source by id from bucket and object key.

    A MissingHierarchyError raised from get_adapter_structure or an AdapterConnectionError
    raised from get_object_key_strings_in_bucket may occur.
    """
    thing_node_id = source_id.rsplit(sep=IDENTIFIER_SEPARATOR, maxsplit=2)[0]
    thing_node_ids = [tn.id for tn in get_adapter_structure().thing_nodes]
    if thing_node_id not in thing_node_ids:
        msg = f"No thing node matching the source id '{source_id}' occurs in the adapter structure!"
        logger.error(msg)
        raise StructureObjectNotFound(msg)

    bucket_name, object_key_string = get_bucket_name_and_object_key_prefix_from_id(
        source_id
    )
    bucket = StructureBucket(name=bucket_name)

    object_key_strings = await get_object_key_strings_in_bucket(bucket.name)
    if object_key_string not in object_key_strings:
        msg = (
            f"There is no object with key '{object_key_string}' in bucket '{bucket_name}', "
            f"hence no source with id '{source_id}' can be found!"
        )
        logger.error(msg)
        raise StructureObjectNotFound(msg)

    object_key = ObjectKey.from_string(object_key_string)
    return BlobStorageStructureSource.from_structure_bucket_and_object_key(
        bucket=bucket, object_key=object_key
    )


def get_thing_node_id_from_source_id(source_id: IdString) -> IdString:
    parent_id = source_id.rsplit(sep=IDENTIFIER_SEPARATOR, maxsplit=2)[0]
    return IdString(parent_id)


async def get_sources_by_parent_id_from_bucket_and_object_keys(
    parent_id: IdString,
) -> list[BlobStorageStructureSource]:
    """Get sources by parent id from bucket and object keys.

    A MissingHierarchyError raised from get_adapter_structure or an AdapterConnectionError
    raised from get_object_key_strings_in_bucket may occur.
    """
    thing_node_ids = [tn.id for tn in get_adapter_structure().thing_nodes]
    if parent_id not in thing_node_ids:
        msg = f"The parent id '{parent_id}' does not occur in the adapter structure!"
        logger.error(msg)
        raise StructureObjectNotFound(msg)

    try:
        (
            bucket_name,
            object_key_string_prefix,
        ) = get_bucket_name_and_object_key_prefix_from_id(parent_id)
    except ValueError:
        return []

    bucket = StructureBucket(name=bucket_name)

    object_key_strings = await get_object_key_strings_in_bucket(bucket.name)
    sources: list[BlobStorageStructureSource] = []
    for object_key_string in object_key_strings:
        if object_key_string.startswith(
            object_key_string_prefix
        ) and parent_id == get_thing_node_id_from_source_id(
            IdString(bucket_name + OBJECT_KEY_DIR_SEPARATOR + object_key_string)
        ):
            try:
                object_key = ObjectKey.from_string(object_key_string)
            except ValueError:
                # ignore objects with keys that do not match the expected name scheme
                continue
            sources.append(
                BlobStorageStructureSource.from_structure_bucket_and_object_key(
                    bucket=bucket, object_key=object_key
                )
            )

    return sources
