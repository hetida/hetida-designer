import re
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConstrainedStr, Field


class ThingNodeName(ConstrainedStr):
    min_length = 1
    max_length = 63
    regex = re.compile(r"[a-zA-Z0-9]+")


class BucketName(ConstrainedStr):
    min_length = 3
    max_length = 63
    regex = re.compile(r"[a-z0-9]+")


class IdString(ConstrainedStr):
    min_length = 1
    regex = re.compile(r"[a-z0-9-]+")


class InfoResponse(BaseModel):
    id: str
    name: str
    version: str


class StructureThingNode(BaseModel):
    id: IdString
    parentId: Optional[IdString] = None
    name: ThingNodeName
    description: str


class BlobStorageStructureSource(BaseModel):
    id: str
    thingNodeId: str
    name: str
    type: Literal["metadata(any)"] = "metadata(any)"
    visible: Literal[True] = True
    path: str = Field(..., description="Display path used in Designer Frontend")
    metadataKey: Literal[None] = None
    filters: Optional[Dict[str, Dict]] = {}


class MultipleSourcesResponse(BaseModel):
    resultCount: int
    sources: List[BlobStorageStructureSource]


class BlobStorageStructureSink(BaseModel):
    id: str
    thingNodeId: str
    name: str
    type: Literal["metadata(any)"] = "metadata(any)"
    visible: Literal[True] = True
    path: str = Field(..., description="Display path used in Designer Frontend")
    metadataKey: Literal[None] = None
    filters: Optional[Dict[str, Dict]] = {}


class MultipleSinksResponse(BaseModel):
    resultCount: int
    sinks: List[BlobStorageStructureSink]


class StructureResponse(BaseModel):
    id: str
    name: str
    thingNodes: List[StructureThingNode]
    sources: List[BlobStorageStructureSource]
    sinks: List[BlobStorageStructureSink]


class Category(BaseModel):
    name: ThingNodeName
    description: str
    substructure: Optional[List[Dict[str, Any]]] = None

    def to_thing_node(self, parent_id: Optional[IdString]) -> StructureThingNode:
        return StructureThingNode(
            id=(parent_id if parent_id is not None else "") + "-" + self.name.lower(),
            parentId=parent_id,
            name=self.name,
            description=self.description,
        )


class Bucket(BaseModel):
    id: str
    name: str

    def to_thing_node(self) -> StructureThingNode:
        return StructureThingNode(
            id=self.id, name=self.name, parentId=None, description="Bucket"
        )


class Blob(BaseModel):
    id: str
    name: str
    bucket_id: str
    bucket_name: str

    def to_source(self) -> BlobStorageStructureSource:
        return BlobStorageStructureSource(
            id=self.id,
            thingNodeId=self.bucket_id,
            name=self.name,
            type="metadata(any)",
            visible=True,
            metadataKey=self.name,
            path=self.bucket_name,
            filters={},
        )

    def to_sink(self) -> BlobStorageStructureSink:
        return BlobStorageStructureSink(
            id=self.id,
            thingNodeId=self.bucket_id,
            name=self.name,
            type="metadata(any)",
            visible=True,
            metadataKey=self.name,
            path=self.bucket_name,
            filters={},
        )
