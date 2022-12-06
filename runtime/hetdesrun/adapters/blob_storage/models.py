import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Tuple

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
    regex = re.compile(r"[a-zA-Z0-9/\-_]+")


class ObjectKey(BaseModel):
    string: IdString
    name: IdString
    time: datetime

    @classmethod
    def from_name(cls, name: IdString) -> "ObjectKey":
        now = datetime.now(timezone.utc)
        return ObjectKey(
            string=name + "_" + now.strftime("%YY%mM%dD%Hh%Mm%Ss"), name=name, time=now
        )

    @classmethod
    def from_string(cls, string: IdString) -> "ObjectKey":
        try:
            name, timestring = string.rsplit("_", maxsplit=1)
        except ValueError as e:
            raise ValueError(
                f"String {string} not a valid ObjectKey string, because it contains no '_'!"
            ) from e
        return ObjectKey(
            string=string,
            name=name,
            time=datetime.strptime(timestring, "%YY%mM%dD%Hh%Mm%Ss"),
        )


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
    id: IdString
    thingNodeId: IdString
    name: str
    type: Literal["metadata(any)"] = "metadata(any)"
    visible: Literal[True] = True
    path: str = Field(..., description="Display path used in Designer Frontend")
    metadataKey: Optional[str] = None
    filters: Optional[Dict[str, Dict]] = {}

    @classmethod
    def from_bucket_name_and_object_key(
        cls, bucket_name: BucketName, object_key: ObjectKey
    ) -> "BlobStorageStructureSource":
        name = (
            object_key.name
            + " - "
            + object_key.time.astimezone(timezone.utc).isoformat(sep=" ")
        )
        thing_node_id = bucket_name + "/" + object_key.name
        return BlobStorageStructureSource(
            id=bucket_name + "/" + object_key.string,
            thingNodeId=thing_node_id,
            name=name,
            path=thing_node_id,
            metadataKey=name,
        )

    def to_bucket_name_and_object_key(self) -> Tuple[BucketName, ObjectKey]:
        try:
            bucket_name_string, object_key_string = self.id.split(sep="/", maxsplit=1)
        except ValueError as e:
            raise ValueError(
                f"Id {self.id} not valid for a source, because it contains no '/'!"
            ) from e
        return BucketName(bucket_name_string), ObjectKey.from_string(
            IdString(object_key_string)
        )


class MultipleSourcesResponse(BaseModel):
    resultCount: int
    sources: List[BlobStorageStructureSource]


class BlobStorageStructureSink(BaseModel):
    id: IdString
    thingNodeId: IdString
    name: str
    type: Literal["metadata(any)"] = "metadata(any)"
    visible: Literal[True] = True
    path: str = Field(..., description="Display path used in Designer Frontend")
    metadataKey: Optional[str] = None
    filters: Optional[Dict[str, Dict]] = {}

    @classmethod
    def from_thing_node(
        cls, thing_node: StructureThingNode, name: str
    ) -> "BlobStorageStructureSink":
        return BlobStorageStructureSink(
            id=thing_node.id + "/next",
            thingNodeId=thing_node.id,
            name=name,
            path=thing_node.id,
            metadataKey=name,
        )

    def to_bucket_name_and_object_key(self) -> Tuple[BucketName, ObjectKey]:
        if not "/" in self.thingNodeId:
            raise ValueError(
                f"thingNodeId {self.thingNodeId} not valid for a sink, because it contains no '/'!"
            )
        bucket_name_string, object_key_name = self.thingNodeId.split(
            sep="/", maxsplit=1
        )
        return BucketName(bucket_name_string), ObjectKey.from_name(
            IdString(object_key_name)
        )


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

    def to_thing_node(
        self, parent_id: Optional[IdString], separator: Literal["-", "/"]
    ) -> StructureThingNode:
        return StructureThingNode(
            id=(parent_id + separator if parent_id is not None else "")
            + (self.name.lower() if separator == "-" else self.name),
            parentId=parent_id,
            name=self.name,
            description=self.description,
        )
