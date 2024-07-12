from logging import getLogger

from hetdesrun.adapters.blob_storage import (
    IDENTIFIER_SEPARATOR,
)
from hetdesrun.adapters.blob_storage.exceptions import (
    StructureObjectNotFound,
)
from hetdesrun.adapters.blob_storage.models import (
    BlobStorageStructureSink,
    BlobStorageStructureSource,
    IdString,
    ObjectKey,
    StructureBucket,
    StructureThingNode,
    get_adapter_structure,
    get_structure_bucket_and_object_key_prefix_from_id,
)
from hetdesrun.adapters.blob_storage.service import get_object_key_strings_in_bucket

logger = getLogger(__name__)


def get_thing_nodes_by_parent_id(
    parent_id: IdString | None,
) -> list[StructureThingNode]:
    """Get thing nodes by parent id.

    A MissingHierarchyError raised by get_adapter_structure may occur.
    """
    try:
        tn_list = get_adapter_structure().thing_nodes_by_parent_id[parent_id]
    except KeyError:
        return []
    return tn_list


async def get_sources_from_bucket(
    bucket: StructureBucket, thing_node_id: IdString | None = None
) -> list[BlobStorageStructureSource]:
    thing_node_ids = list(get_adapter_structure().thing_node_by_id.keys())
    src_list: list[BlobStorageStructureSource] = []

    object_key_strings = await get_object_key_strings_in_bucket(bucket.name)
    logger.info(
        "There are the following object keys in bucket %s:\n%s",
        bucket.name,
        ", ".join(oks for oks in object_key_strings),
    )
    for object_key_string in object_key_strings:
        try:
            object_key = ObjectKey.from_string(object_key_string)
        except ValueError:
            # ignore objects with keys that do not match the expected name scheme
            logger.warning("The string %s cannot be parsed into an object key.", object_key_string)
            continue

        # ignore objects that do not match the configured hierarchy
        thing_node_id_from_ok_and_bucket = object_key.to_thing_node_id(bucket)
        if thing_node_id_from_ok_and_bucket in thing_node_ids and (
            (thing_node_id is not None and thing_node_id == thing_node_id_from_ok_and_bucket)
            or thing_node_id is None
        ):
            source = BlobStorageStructureSource.from_structure_bucket_and_object_key(
                bucket=bucket, object_key=object_key
            )
            src_list.append(source)
            logger.debug("Created source:\n%s", source.json())
    return src_list


async def get_sources_by_parent_id(
    parent_id: IdString | None,
) -> list[BlobStorageStructureSource]:
    """Get sources by parent id.

    A MissingHierarchyError raised from get_adapter_structure or an AdapterConnectionError
    raised from get_object_key_strings_in_bucket may occur.
    """
    if parent_id is None:
        return []

    thing_node_ids = [tn.id for tn in get_adapter_structure().thing_nodes]
    if parent_id not in thing_node_ids:
        msg = f"The parent id '{parent_id}' does not occur in the adapter structure!"
        logger.error(msg)
        raise StructureObjectNotFound(msg)

    try:
        bucket, _ = get_structure_bucket_and_object_key_prefix_from_id(parent_id)
    except ValueError:
        return []

    return await get_sources_from_bucket(bucket, parent_id)


def get_sinks_by_parent_id(
    parent_id: IdString | None,
) -> list[BlobStorageStructureSink]:
    """Get sinks by parent id.

    A MissingHierarchyError raised by get_adapter_structre may occur.
    """
    if parent_id is None:
        return []

    try:
        snk_by_parent_id_list = get_adapter_structure().sinks_by_parent_id[parent_id]
    except KeyError:
        return []

    return snk_by_parent_id_list


async def get_all_sources() -> list[BlobStorageStructureSource]:
    """Get sources from buckets and object keys.

    A MissingHierarchyError raised from get_adapter_structure or an AdapterConnectionError
    raised from get_object_key_strings_in_bucket may occur.
    """
    buckets = get_adapter_structure().structure_buckets
    src_list: list[BlobStorageStructureSource] = []
    for bucket in buckets:
        src_list.extend(await get_sources_from_bucket(bucket))
    return src_list


async def get_filtered_sources(
    filter_str: str | None,
) -> list[BlobStorageStructureSource]:
    """Get sources from buckets and object keys.

    A MissingHierarchyError or an AdapterConnectionError raised from get_all_sources may occur.
    """
    if filter_str is None:
        filter_str = ""

    src_list = await get_all_sources()

    return [src for src in src_list if filter_str in src.id]


def get_filtered_sinks(filter_str: str | None) -> list[BlobStorageStructureSink]:
    """Get filtered sinks.

    A MissingHierarchyError raised by get_adapter_structre may occur.
    """
    if filter_str is None:
        filter_str = ""

    return [snk for snk in get_adapter_structure().sinks if filter_str in snk.id]


def get_thing_node_by_id(thing_node_id: IdString) -> StructureThingNode:
    """Get thing node by id.

    A MissingHierarchyError raised by get_adapter_structre may occur.
    """
    try:
        thing_node = get_adapter_structure().thing_node_by_id[thing_node_id]
    except KeyError as error:
        msg = f"Found no thing node with id {thing_node_id}!"
        logger.error(msg)
        raise StructureObjectNotFound(msg) from error
    return thing_node


async def get_source_by_id(source_id: IdString) -> BlobStorageStructureSource:
    """Get source by id.

    A MissingHierarchyError raised from get_adapter_structure or an AdapterConnectionError
    raised from get_object_key_strings_in_bucket may occur.
    """
    thing_node_id = source_id.rsplit(sep=IDENTIFIER_SEPARATOR, maxsplit=2)[0]
    thing_node_ids = list(get_adapter_structure().thing_node_by_id.keys())
    if thing_node_id not in thing_node_ids:
        msg = f"No thing node matching the source id '{source_id}' occurs in the adapter structure!"
        logger.error(msg)
        raise StructureObjectNotFound(msg)

    bucket, object_key_string = get_structure_bucket_and_object_key_prefix_from_id(source_id)
    try:
        object_key = ObjectKey.from_string(object_key_string)
    except ValueError as error:
        msg = (
            f"Cannot get object key from string '{object_key_string}' extracted from "
            f"source id '{source_id}':\n{error}"
        )
        logger.error(msg)
        raise StructureObjectNotFound(msg) from error

    object_key_strings = await get_object_key_strings_in_bucket(bucket.name)
    if object_key_string not in object_key_strings:
        msg = (
            f"There is no object with key '{object_key_string}' in bucket '{bucket.name}', "
            f"hence no source with id '{source_id}' can be found!"
        )
        logger.error(msg)
        raise StructureObjectNotFound(msg)

    return BlobStorageStructureSource.from_structure_bucket_and_object_key(
        bucket=bucket, object_key=object_key
    )


def get_sink_by_id(sink_id: IdString) -> BlobStorageStructureSink:
    """Get sink by id.

    A MissingHierarchyError raised by get_adapter_structre may occur.
    """
    try:
        sink = get_adapter_structure().sink_by_id[sink_id]
    except KeyError as error:
        msg = f"Found no sink with id {sink_id}!"
        logger.error(msg)
        raise StructureObjectNotFound(msg) from error
    return sink


async def get_source_by_thing_node_id_and_metadata_key(
    thing_node_id: IdString, metadata_key: str
) -> BlobStorageStructureSource:
    """Get source by thing node id and metadata key.

    A MissingHierarchyError, StorageAuthenticationError, or AdapterConnectionError
    raised by get_all_sources_from_buckets_and_object_keys may occur.
    """
    thing_node_ids = list(get_adapter_structure().thing_node_by_id.keys())
    if thing_node_id not in thing_node_ids:
        msg = f"No thing node with id '{thing_node_id}' occurs in the adapter structure!"
        logger.error(msg)
        raise StructureObjectNotFound(msg)

    bucket, _ = get_structure_bucket_and_object_key_prefix_from_id(thing_node_id)
    try:
        object_key = ObjectKey.from_thing_node_id_and_metadata_key(thing_node_id, metadata_key)
    except ValueError as error:
        msg = (
            f"Cannot get object key from thing node id '{thing_node_id}' and "
            f"metadata key '{metadata_key}':\n{error}"
        )
        logger.error(msg)
        raise StructureObjectNotFound(msg) from error

    object_key_strings = await get_object_key_strings_in_bucket(bucket.name)
    if object_key.string not in object_key_strings:
        msg = (
            f"There is no object with key '{object_key.string}' in bucket '{bucket.name}', "
            f"hence no source with thing node id '{thing_node_id}' and "
            f"metadata key '{metadata_key}' can be found!"
        )
        logger.error(msg)
        raise StructureObjectNotFound(msg)

    return BlobStorageStructureSource.from_structure_bucket_and_object_key(
        bucket=bucket, object_key=object_key
    )


def get_sink_by_thing_node_id_and_metadata_key(
    thing_node_id: IdString, metadata_key: str
) -> BlobStorageStructureSink:
    """Get sink by thing node id and metadata key.

    A MissingHierarchyError raised by get_adapter_structure may occur.
    """
    try:
        sink = get_adapter_structure().sink_by_thing_node_id_and_metadata_key[
            (thing_node_id, metadata_key)
        ]

    except KeyError as error:
        msg = (
            f"Found no sink with thing node id {thing_node_id} " f"and metadata key {metadata_key}!"
        )
        logger.error(msg)
        raise StructureObjectNotFound(msg) from error
    return sink
