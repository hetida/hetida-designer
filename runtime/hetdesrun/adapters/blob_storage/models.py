import re
from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional, Set, Tuple

from pydantic import BaseModel, ConstrainedStr, Field, validator


class ThingNodeName(ConstrainedStr):
    min_length = 1
    max_length = 63
    regex = re.compile(r"^[a-zA-Z0-9]+$")


class BucketName(ConstrainedStr):
    min_length = 3
    max_length = 63
    regex = re.compile(r"^[a-z0-9]+$")


class IdString(ConstrainedStr):
    min_length = 1
    regex = re.compile(r"^[a-zA-Z0-9/\-_]+$")


class ObjectKey(BaseModel):
    string: IdString
    name: IdString
    time: datetime

    # pylint: disable=no-self-argument
    @validator("time")
    def has_timezone_utc(cls, time: datetime) -> datetime:
        if time.tzinfo != timezone.utc:
            raise ValueError("The ObjectKey attribute time must have timezone UTC!")
        return time

    @classmethod
    def from_name(cls, name: IdString) -> "ObjectKey":
        now = datetime.now(timezone.utc).replace(microsecond=0)
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
            time=datetime.strptime(timestring, "%YY%mM%dD%Hh%Mm%Ss").replace(
                tzinfo=timezone.utc
            ),
        )

    def to_thing_node_id(self, bucket_name: BucketName) -> IdString:
        return IdString(bucket_name + "/" + self.name)


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
    path: str = Field(..., description="Display path used in Designer Frontend")
    metadataKey: str
    type: Literal["metadata(any)"] = "metadata(any)"
    visible: Literal[True] = True
    filters: Optional[Dict[str, Dict]] = {}

    # pylint: disable=no-self-argumeng
    @validator("thingNodeId")
    def thing_node_id_matches_id(cls, thingNodeId: IdString, values: dict) -> IdString:
        try:
            id = values["id"]  # pylint: disable=redefine-builtin
        except KeyError as e:
            raise ValueError(
                "Cannot check if thing node id matches id if attribute id is missing!"
            ) from e

        thing_node_id_from_id = str(id).split(sep="_")[0]
        if thing_node_id_from_id != thingNodeId:
            raise ValueError(
                f"BlobStorageStructureSource thing node id {thingNodeId} does not match id {id}!"
            )
        return thingNodeId

    # pylint: disable=no-self-argument
    @validator("name")
    def name_matches_id(cls, name: str, values: dict) -> str:
        try:
            id = values["id"]  # pylint: disable=redefine-builtin
        except KeyError as e:
            raise ValueError(
                "Cannot check if name matches id if attribute id is missing!"
            ) from e

        return name

    @classmethod
    def from_bucket_name_and_object_key(
        cls, bucket_name: BucketName, object_key: ObjectKey
    ) -> "BlobStorageStructureSource":
        name = (
            object_key.name
            + " - "
            + object_key.time.astimezone(timezone.utc).isoformat(sep=" ")
        )
        thing_node_id = object_key.to_thing_node_id(bucket_name)
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
    path: str = Field(..., description="Display path used in Designer Frontend")
    metadataKey: str
    type: Literal["metadata(any)"] = "metadata(any)"
    visible: Literal[True] = True
    filters: Optional[Dict[str, Dict]] = {}

    @classmethod
    def from_thing_node(
        cls, thing_node: StructureThingNode, name: str
    ) -> "BlobStorageStructureSink":
        return BlobStorageStructureSink(
            id=thing_node.id + "_next",
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
    substructure: Optional[List["Category"]] = None
    level: Optional[int] = None

    def set_level_and_get_depth(self, level: int) -> int:
        self.level = level
        if self.substructure is not None and len(self.substructure) != 0:
            depths: List[int] = []
            for category in self.substructure:
                depths.append(category.set_level_and_get_depth(self.level + 1))
            return max(depths)
        return level

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


class BlobAdapterConfig(BaseModel):
    """Define the Blob Storage Hierarchy.

    The Amazon S3 data model is a flat structure: You create a bucket, and the bucket stores
    objects. There is no hierarchy of subbuckets or subfolders. However, the logical hierarchy of
    the adapter is infered to the object keys by using key name prefixes and delimiters.
    the Amazon S3 console and the AWS SDKs can infer hierarchy from such prefixes and delementers
    and introduce the concept of folders.
    """

    structure: List[Category]
    total_number_of_levels: Optional[int] = None
    bucket_level: int
    bucket_name_separator: Literal["-"] = "-"
    object_key_separator: Literal["!", "-", "_", ".", "'", "(", ")", "/"] = "/"
    date_separator: Literal["_"] = "_"

    # pylint: disable=no-self-argument
    @validator("total_number_of_levels")
    def set_levels_and_determine_total_number_of_levels(
        cls, total_number_of_levels: Optional[int], values: dict
    ) -> int:
        try:
            structure: List[Category] = values["structure"]
        except KeyError as e:
            raise ValueError(
                "Cannot determine total number of levels in structure if attribute "
                "'structure' is missing!"
            ) from e

        depths: Set[int] = set()
        for category in structure:
            depths.add(category.set_level_and_get_depth(level=1))

        if len(depths) != 0:
            raise ValueError("All end nodes of the structure must have the same level!")

        depth = depths.pop()
        if total_number_of_levels is not None and total_number_of_levels != depth:
            raise ValueError("The provided total_number_of_levels is incorrect!")

        return depth

    # pylint: disable=no-self-argument
    @validator("bucket_level")
    def bucket_level_smaller_than_total_nof_levels(
        cls, bucket_level: int, values: dict
    ) -> int:
        try:
            total_number_of_levels = values["total_number_of_levels"]
        except KeyError as e:
            raise ValueError(
                "Cannot check if bucket level is smaller than total number of levels if attribute"
                "'total_number_of_levels' is missing!"
            ) from e

        if total_number_of_levels is None:
            return bucket_level
        #     raise ValueError(
        #         "Cannot check if bucket level is smaller than total number of levels if attribute"
        #         "'total_number_of_levels' is None!"
        #     )

        if not bucket_level < total_number_of_levels:
            raise ValueError(
                "The bucket level must be smaller than the total number of levels!"
            )

        return bucket_level
