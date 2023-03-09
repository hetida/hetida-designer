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
from hetdesrun.adapters.blob_storage.utils import create_sources

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
    raised by create_sources may occur.
    """
    if parent_id is None:
        return []

    src_list = await create_sources()

    return [src for src in src_list if src.thingNodeId == parent_id]


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
    raised by create_sources may occur.
    """
    if filter_str is None:
        filter_str = ""

    src_list = await create_sources()

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
    raised by create_sources may occur.
    """
    src_list = await create_sources()

    filtered_src_list = [src for src in src_list if src.id == source_id]
    if len(filtered_src_list) == 0:
        msg = f"Found no source with id {source_id}!"
        logger.error(msg)
        raise StructureObjectNotFound(msg)
    if len(filtered_src_list) > 1:
        msg = (
            f"Found more than one source with id {source_id}:\n{str(filtered_src_list)}"
        )
        logger.error(msg)
        raise StructureObjectNotUnique(msg)
    return filtered_src_list[0]


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
    raised by create_sources may occur.
    """
    filtered_src_list = []

    src_list = await create_sources()

    for src in src_list:
        if src.thingNodeId == thing_node_id and src.metadataKey == metadata_key:
            filtered_src_list.append(src)

    if len(filtered_src_list) == 0:
        msg = (
            f"Found no source with thing node id '{thing_node_id}' "
            f"and metadata key '{metadata_key}'!"
        )
        logger.error(msg)
        raise StructureObjectNotFound(msg)
    if len(filtered_src_list) > 1:
        msg = (
            f"Found more than one source with thing node id '{thing_node_id}' "
            f"and metadata key '{metadata_key}':\n{str(filtered_src_list)}"
        )
        logger.error(msg)
        raise StructureObjectNotUnique(msg)
    return filtered_src_list[0]


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
