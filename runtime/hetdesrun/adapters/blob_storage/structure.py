from logging import getLogger
from typing import List, Optional

from hetdesrun.adapters.blob_storage import snks, srcs, tns
from hetdesrun.adapters.blob_storage.exceptions import (
    SinkNotFound,
    SinksNotUnique,
    SourceNotFound,
    SourcesNotUnique,
    ThingNodeNotFound,
    ThingNodesNotUnique,
)
from hetdesrun.adapters.blob_storage.models import (
    BlobStorageStructureSink,
    BlobStorageStructureSource,
    IdString,
    StructureThingNode,
)

logger = getLogger(__name__)


def get_thing_nodes_by_parent_id(
    parent_id: Optional[IdString] = None,
) -> List[StructureThingNode]:
    return [tn for tn in tns if tn.parentId == parent_id]


def get_sources_by_parent_id(
    parent_id: Optional[IdString] = None,
) -> List[BlobStorageStructureSource]:
    if parent_id is None:
        return []
    return [src for src in srcs if src.thingNodeId == parent_id]


def get_sinks_by_parent_id(
    parent_id: Optional[IdString] = None,
) -> List[BlobStorageStructureSink]:
    if parent_id is None:
        return []
    return [snk for snk in snks if snk.thingNodeId == parent_id]


def get_filtered_sources(filter_str: Optional[str]) -> List[BlobStorageStructureSource]:
    if filter_str is None:
        filter_str = ""

    return [src for src in srcs if filter_str in src.id]


def get_filtered_sinks(filter_str: Optional[str]) -> List[BlobStorageStructureSink]:
    if filter_str is None:
        filter_str = ""

    return [snk for snk in snks if filter_str in snk.id]


def get_thing_node_by_id(thing_node_id: IdString) -> StructureThingNode:
    tn_list = [tn for tn in tns if tn.id == thing_node_id]
    if len(tn_list) == 0:
        msg = f"Found no thing node with id {thing_node_id}!"
        logger.error(msg)
        raise ThingNodeNotFound(msg)
    if len(tn_list) > 1:
        msg = f"Found more than one thing node with id {thing_node_id}:\n{str(tn_list)}"
        logger.error(msg)
        raise ThingNodesNotUnique(msg)
    return tn_list[0]


def get_source_by_id(source_id: IdString) -> BlobStorageStructureSource:
    src_list = [src for src in srcs if src.id == source_id]
    if len(src_list) == 0:
        msg = f"Found no source with id {source_id}!"
        logger.error(msg)
        raise SourceNotFound(msg)
    if len(src_list) > 1:
        msg = f"Found more than one source with id {source_id}:\n{str(src_list)}"
        logger.error(msg)
        raise SourcesNotUnique(msg)
    return src_list[0]


def get_sink_by_id(sink_id: IdString) -> BlobStorageStructureSink:
    snk_list = [snk for snk in snks if snk.id == sink_id]
    if len(snk_list) == 0:
        msg = f"Found no sink with id {sink_id}!"
        logger.error(msg)
        raise SinkNotFound(msg)
    if len(snk_list) > 1:
        msg = f"Found more than one sink with id {sink_id}:\n{str(snk_list)}"
        logger.error(msg)
        raise SinksNotUnique(msg)
    return snk_list[0]
