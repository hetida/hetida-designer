from logging import getLogger

from hetdesrun.adapters.blob_storage.exceptions import (
    StructureObjectNotFound,
    StructureObjectNotUnique,
)
from hetdesrun.adapters.blob_storage.models import (
    BlobStorageStructureSink,
    BlobStorageStructureSource,
    IdString,
    StructureThingNode,
    get_adapter_structure,
)
from hetdesrun.adapters.blob_storage.service import get_object_key_strings_in_bucket
from hetdesrun.adapters.blob_storage.utils import (
    get_all_sources_from_buckets_and_object_keys,
    get_source_by_id_from_bucket_and_object_key,
    get_sources_by_parent_id_from_bucket_and_object_keys,
)

logger = getLogger(__name__)


def get_thing_nodes_by_parent_id(
    parent_id: IdString | None,
) -> list[StructureThingNode]:
    """Get thing nodes by parent id.

    A MissingHierarchyError raised by get_adapter_structure may occur.
    """

    tn_list = get_adapter_structure().thing_nodes

    return [tn for tn in tn_list if tn.parentId == parent_id]


async def get_sources_by_parent_id(
    parent_id: IdString | None,
) -> list[BlobStorageStructureSource]:
    """Get sources by parent id.

    A MissingHierarchyError, StorageAuthenticationError, or AdapterConnectionError
    raised by get_sources_by_parent_id_from_bucket_and_object_keys.
    """
    if parent_id is None:
        return []

    return await get_sources_by_parent_id_from_bucket_and_object_keys(parent_id)


def get_sinks_by_parent_id(
    parent_id: IdString | None,
) -> list[BlobStorageStructureSink]:
    """Get sinks by parent id.

    A MissingHierarchyError raised by get_adapter_structre may occur.
    """
    if parent_id is None:
        return []

    snk_list = get_adapter_structure().sinks

    return [snk for snk in snk_list if snk.thingNodeId == parent_id]


async def get_filtered_sources(
    filter_str: str | None,
) -> list[BlobStorageStructureSource]:
    """Get filtered sources.

    A MissingHierarchyError, StorageAuthenticationError, or AdapterConnectionError
    raised by get_all_sources_from_buckets_and_object_keys may occur.
    """
    if filter_str is None:
        filter_str = ""

    src_list = await get_all_sources_from_buckets_and_object_keys()

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
    tn_list = get_adapter_structure().thing_nodes

    filtered_tn_list = [tn for tn in tn_list if tn.id == thing_node_id]
    if len(filtered_tn_list) == 0:
        msg = f"Found no thing node with id {thing_node_id}!"
        logger.error(msg)
        raise StructureObjectNotFound(msg)
    if len(filtered_tn_list) > 1:
        msg = f"Found more than one thing node with id {thing_node_id}:\n{str(filtered_tn_list)}"
        logger.error(msg)
        raise StructureObjectNotUnique(msg)
    return filtered_tn_list[0]


async def get_source_by_id(source_id: IdString) -> BlobStorageStructureSource:
    """Get source by id.

    A MissingHierarchyError, StorageAuthenticationError, or AdapterConnectionError
    raised by get_source_by_id_from_bucket_and_object_key may occur.
    """
    return await get_source_by_id_from_bucket_and_object_key(source_id)


def get_sink_by_id(sink_id: IdString) -> BlobStorageStructureSink:
    """Get sink by id.

    A MissingHierarchyError raised by get_adapter_structre may occur.
    """
    snk_list = get_adapter_structure().sinks

    filtered_snk_list = [snk for snk in snk_list if snk.id == sink_id]
    if len(filtered_snk_list) == 0:
        msg = f"Found no sink with id {sink_id}!"
        logger.error(msg)
        raise StructureObjectNotFound(msg)
    if len(filtered_snk_list) > 1:
        msg = f"Found more than one sink with id {sink_id}:\n{str(filtered_snk_list)}"
        logger.error(msg)
        raise StructureObjectNotUnique(msg)
    return filtered_snk_list[0]


async def get_source_by_thing_node_id_and_metadata_key(
    thing_node_id: IdString, metadata_key: str
) -> BlobStorageStructureSource:
    """Get source by thing node id and metadata key.

    A MissingHierarchyError, StorageAuthenticationError, or AdapterConnectionError
    raised by get_all_sources_from_buckets_and_object_keys may occur.
    """
    thing_node = get_thing_node_by_id(thing_node_id)
    try:
        bucket, object_key = thing_node.to_bucket_and_object_key(metadata_key)
    except ValueError as error:
        raise StructureObjectNotFound from error

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
    snk_list = get_adapter_structure().sinks

    filtered_snk_list = [
        snk
        for snk in snk_list
        if snk.thingNodeId == thing_node_id and snk.metadataKey == metadata_key
    ]
    if len(filtered_snk_list) == 0:
        msg = (
            f"Found no source with thing node id {thing_node_id} "
            f"and metadata key {metadata_key}!"
        )
        logger.error(msg)
        raise StructureObjectNotFound(msg)
    if len(filtered_snk_list) > 1:
        msg = (
            f"Found more than one source with thing node id {thing_node_id} "
            f"and metadata key {metadata_key}:\n{str(filtered_snk_list)}"
        )
        logger.error(msg)
        raise StructureObjectNotUnique(msg)
    return filtered_snk_list[0]
