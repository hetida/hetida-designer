from logging import getLogger
from typing import List, Optional

from hetdesrun.adapters.blob_storage import snks, srcs, tns
from hetdesrun.adapters.blob_storage.exceptions import BlobAdapterException
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
    return [
        src
        for src in srcs
        if str(src.id).startswith(parent_id) and len(src.id) != parent_id
    ]


def get_sinks_by_parent_id(
    parent_id: Optional[IdString] = None,
) -> List[BlobStorageStructureSink]:
    if parent_id is None:
        return []
    return [
        snk
        for snk in snks
        if str(snk.id).startswith(parent_id) and len(snk.id) != parent_id
    ]


def get_filtered_sources(filter_str: Optional[str]) -> List[BlobStorageStructureSource]:
    if filter_str is None:
        filter_str = ""

    return [src for src in srcs if filter_str in src.id]


def get_filtered_sinks(filter_str: Optional[str]) -> List[BlobStorageStructureSink]:
    if filter_str is None:
        filter_str = ""

    return [snk for snk in snks if filter_str in snk.id]


def get_thing_node_by_id(thing_node_id: IdString) -> Optional[StructureThingNode]:
    tn_list = [tn for tn in tns if tn.id == thing_node_id]
    if len(tn_list) > 1:
        raise BlobAdapterException
    if len(tn_list) == 1:
        return tn_list[0]
    # len(tn_list) == 0
    return None


def get_source_by_id(source_id: IdString) -> Optional[BlobStorageStructureSource]:
    src_list = [src for src in srcs if src.id == source_id]
    if len(src_list) > 1:
        raise BlobAdapterException
    if len(src_list) == 1:
        return src_list[0]
    # len(tn_list) == 0
    return None


def get_sink_by_id(sink_id: IdString) -> Optional[BlobStorageStructureSink]:
    snk_list = [snk for snk in snks if snk.id == sink_id]
    if len(snk_list) > 1:
        raise BlobAdapterException
    if len(snk_list) == 1:
        return snk_list[0]
    # len(tn_list) == 0
    return None
