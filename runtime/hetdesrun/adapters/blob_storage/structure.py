from typing import List, Optional

from hetdesrun.adapters.blob_storage.models import (
    Blob,
    BlobStorageStructureSink,
    BlobStorageStructureSource,
    StructureResponse,
    StructureThingNode,
)
from hetdesrun.adapters.blob_storage.service import (
    get_all_blobs,
    get_blob_by_id,
    get_blobs_in_bucket,
    get_bucket_by_id,
    get_buckets,
)


def get_structure(parent_id: Optional[str] = None) -> StructureResponse:
    """Obtain structure for corresponding adapter web service endpoint.

    parent_id is the name of a bucket or None.
    """
    if parent_id is None:  # get root nodes
        return StructureResponse(
            id="blob-storage-adapter",
            name="Blob Storage Adapter",
            thingNodes=[bucket.to_thing_node() for bucket in get_buckets()],
            sources=[],
            sinks=[],
        )
    else:
        blobs = get_blobs_in_bucket(parent_id)
        return StructureResponse(
            id="blob-storage-adapter",
            name="Blob Storage Adapter",
            thingNodes=[],
            sources=[blob.to_source() for blob in blobs],
            sinks=[blob.to_sink() for blob in blobs],
        )

def filter_blobs(filter_str: Optional[str], blobs: List[Blob]):
    if filter_str is None:
        filter_str = ""

    return [blob for blob in blobs if filter_str in blob.id]

def get_sources(filter_str: Optional[str]) -> List[BlobStorageStructureSource]:
    return [blob.to_source() for blob in filter_blobs(filter_str, get_all_blobs())]


def get_sinks(filter_str: Optional[str]) -> List[BlobStorageStructureSink]:
    return [blob.to_source() for blob in filter_blobs(filter_str, get_all_blobs())]


def get_thing_node_by_id(thing_node_id: str) -> Optional[StructureThingNode]:
    return get_bucket_by_id(thing_node_id).to_thing_node()


def get_source_by_id(source_id: str) -> Optional[BlobStorageStructureSource]:
    return get_blob_by_id(source_id).to_source()


def get_sink_by_id(sink_id: str) -> Optional[BlobStorageStructureSink]:
    return get_blob_by_id(sink_id).to_sink()
