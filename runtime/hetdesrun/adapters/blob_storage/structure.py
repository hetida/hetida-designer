from logging import getLogger
from typing import List, Optional

from hetdesrun.adapters.blob_storage.exceptions import (
    InvalidEndpointError,
    MissingHierarchyError,
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
from hetdesrun.adapters.exceptions import AdapterConnectionError

logger = getLogger(__name__)


def get_thing_nodes_by_parent_id(
    parent_id: Optional[IdString],
) -> List[StructureThingNode]:
    try:
        tn_list = get_adapter_structure().thing_nodes
    except MissingHierarchyError as error:
        raise error

    return [tn for tn in tn_list if tn.parentId == parent_id]


def get_sources_by_parent_id(
    parent_id: Optional[IdString],
) -> List[BlobStorageStructureSource]:
    if parent_id is None:
        return []

    try:
        src_list = create_sources()
    except (
        MissingHierarchyError,
        InvalidEndpointError,
        AdapterConnectionError,
    ) as error:
        raise error

    return [src for src in src_list if src.thingNodeId == parent_id]


def get_sinks_by_parent_id(
    parent_id: Optional[IdString],
) -> List[BlobStorageStructureSink]:
    if parent_id is None:
        return []

    try:
        snk_list = get_adapter_structure().sinks
    except MissingHierarchyError as error:
        raise error

    return [snk for snk in snk_list if snk.thingNodeId == parent_id]


def get_filtered_sources(filter_str: Optional[str]) -> List[BlobStorageStructureSource]:
    if filter_str is None:
        filter_str = ""

    try:
        src_list = create_sources()
    except (
        MissingHierarchyError,
        InvalidEndpointError,
        AdapterConnectionError,
    ) as error:
        raise error

    return [src for src in src_list if filter_str in src.id]


def get_filtered_sinks(filter_str: Optional[str]) -> List[BlobStorageStructureSink]:
    if filter_str is None:
        filter_str = ""

    return [snk for snk in get_adapter_structure().sinks if filter_str in snk.id]


def get_thing_node_by_id(thing_node_id: IdString) -> StructureThingNode:
    try:
        tn_list = get_adapter_structure().thing_nodes
    except MissingHierarchyError as error:
        raise error

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


def get_source_by_id(source_id: IdString) -> BlobStorageStructureSource:
    try:
        src_list = create_sources()
    except (
        MissingHierarchyError,
        InvalidEndpointError,
        AdapterConnectionError,
    ) as error:
        raise error

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
    try:
        snk_list = get_adapter_structure().sinks
    except MissingHierarchyError as error:
        raise error

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


def get_source_by_thing_node_id_and_metadata_key(
    thing_node_id: IdString, metadata_key: str
) -> BlobStorageStructureSource:
    filtered_src_list = []

    try:
        src_list = create_sources()
    except (
        MissingHierarchyError,
        InvalidEndpointError,
        AdapterConnectionError,
    ) as error:
        raise error

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
    try:
        snk_list = get_adapter_structure().sinks
    except MissingHierarchyError as error:
        raise error

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
