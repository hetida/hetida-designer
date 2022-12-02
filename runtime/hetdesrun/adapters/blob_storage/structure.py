from logging import getLogger
from typing import List, Optional, Union

from hetdesrun.adapters.blob_storage import snks, srcs, tns
from hetdesrun.adapters.blob_storage.models import (
    BlobStorageStructureSink,
    BlobStorageStructureSource,
    IdString,
    StructureThingNode,
)

logger = getLogger(__name__)


def filter_sinks_or_sources(
    filter_str: Optional[str],
    sinks_or_sources: Union[
        List[BlobStorageStructureSource], List[BlobStorageStructureSink]
    ],
) -> Union[List[BlobStorageStructureSource], List[BlobStorageStructureSink]]:
    if filter_str is None:
        filter_str = ""

    return [sos for sos in sinks_or_sources if filter_str in sos.id]


def get_thing_nodes_by_parent_id(
    parent_id: Optional[IdString] = None,
) -> List[StructureThingNode]:
    return [tn for tn in tns if tn.parentId == parent_id]


def get_sources_by_parent_id(
    parent_id: Optional[IdString] = None,
) -> List[BlobStorageStructureSource]:
    [src for src in srcs if src.id.startswith(parent_id) and len(src.id) != parent_id]


def get_sinks_by_parent_id(
    parent_id: Optional[IdString] = None,
) -> List[BlobStorageStructureSink]:
    [snk for snk in snks if snk.id.startswith(parent_id) and len(snk.id) != parent_id]


def get_filtered_sources(filter_str: Optional[str]) -> List[BlobStorageStructureSource]:
    return filter_sinks_or_sources(filter_str=filter_str, sinks_or_sources=srcs)


def get_filtered_sinks(filter_str: Optional[str]) -> List[BlobStorageStructureSink]:
    return filter_sinks_or_sources(filter_str=filter_str, sinks_or_sources=snks)


def get_thing_node_by_id(thing_node_id: IdString) -> Optional[StructureThingNode]:
    return [tn for tn in tns if tn.id == thing_node_id]


def get_source_by_id(source_id: IdString) -> Optional[BlobStorageStructureSource]:
    return [src for src in srcs if src.id == source_id]


def get_sink_by_id(sink_id: IdString) -> Optional[BlobStorageStructureSink]:
    return [snk for snk in snks if snk.id == sink_id]
