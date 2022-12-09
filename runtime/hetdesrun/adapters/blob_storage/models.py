import re
from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional, Set, Tuple

from pydantic import BaseModel, ConstrainedStr, Field, ValidationError, validator


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

    # pylint: disable=no-self-argument
    @validator("id")
    def id_matches_scheme(cls, id: IdString) -> IdString:
        if "/" not in id:
            raise ValueError("The source id must contain at least one '/'!")
        bucket_name, object_key_string = id.split(sep="/", maxsplit=1)
        try:
            BucketName(bucket_name)
        except ValidationError as e:
            raise ValueError(
                "The first part of the source id before the first '/' must "
                "correspond to a bucket name!\nBut it does not:\n" + str(e)
            ) from e

        try:
            ObjectKey.from_string(IdString(object_key_string))
        except ValidationError as e:
            raise ValueError(
                "The second part of the source id after the first '/' must "
                "correspond to an object key string!\nBut it does not:\n" + str(e)
            ) from e
        return id

    # pylint: disable=no-self-argument
    @validator("thingNodeId")
    def thing_node_id_matches_id(cls, thingNodeId: IdString, values: dict) -> IdString:
        try:
            id = values["id"]  # pylint: disable=redefined-builtin
        except KeyError as e:
            raise ValueError(
                "Cannot check if the source's thingNodeId matches its id "
                "if the attribute 'id' is missing!"
            ) from e

        thing_node_id_from_id = str(id).rsplit(sep="_", maxsplit=1)[0]
        if thing_node_id_from_id != thingNodeId:
            raise ValueError(
                f"The source's thing node id {thingNodeId} does not match its id {id}!"
            )
        return thingNodeId

    # pylint: disable=no-self-argument
    @validator("name")
    def name_matches_id(cls, name: str, values: dict) -> str:
        try:
            id = values["id"]  # pylint: disable=redefined-builtin
        except KeyError as e:
            raise ValueError(
                "Cannot check if the source's name matches its id if the attribute 'id' is missing!"
            ) from e
        file_string_from_id = id.rsplit(sep="/", maxsplit=1)[1]
        file_ok = ObjectKey.from_string(IdString(file_string_from_id))
        thing_node_name, source_time = name.split(" - ")
        if thing_node_name != file_ok.name:
            raise ValueError(
                "The source name must start with the name of the corresponding thing node!"
            )
        if file_ok.time.astimezone(timezone.utc).isoformat(sep=" ") != source_time:
            raise ValueError(
                "The time in the source's name must match to the time in the its id!"
            )

        return name

    # pylint: disable=no-self-argument
    @validator("path")
    def path_matches_thing_node_id(cls, path: str, values: dict) -> str:
        try:
            thingNodeId = values["thingNodeId"]
        except KeyError as e:
            raise ValueError(
                "Cannot check if source's path matches its thingNodeId "
                "if the attribute 'thingNodeId' is missing!"
            ) from e

        if path != thingNodeId:
            raise ValueError(
                "The source's path must be the same string as its thingNodeId!"
            )

        return path

    # pylint: disable=no-self-argument
    @validator("metadataKey")
    def metadata_key_matches_name(cls, metadataKey: str, values: dict) -> str:
        try:
            name = values["name"]
        except KeyError as e:
            raise ValueError(
                "Cannot check if source's metadataKey matches its name "
                "if the attribute 'name' is missing!"
            ) from e

        if metadataKey != name:
            raise ValueError(
                "The COUR's metadataKey must be the same string as its name!"
            )

        return metadataKey

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

    # pylint: disable=no-self-argument
    @validator("id")
    def id_matches_scheme(cls, id: IdString) -> IdString:
        if "/" not in id:
            raise ValueError("The sink id must contain at least one '/'!")
        bucket_name, object_key_string = id.split(sep="/", maxsplit=1)
        try:
            BucketName(bucket_name)
        except ValidationError as e:
            raise ValueError(
                "The first part of the sink id before the first '/' must "
                "correspond to a bucket name!\nBut it does not:\n" + str(e)
            ) from e

        if not object_key_string.endswith("_next"):
            raise ValueError(
                "The the sink id must end with '_next'!"
            )
        return id

    # pylint: disable=no-self-argument
    @validator("thingNodeId")
    def thing_node_id_matches_id(cls, thingNodeId: IdString, values: dict) -> IdString:
        try:
            id = values["id"]  # pylint: disable=redefined-builtin
        except KeyError as e:
            raise ValueError(
                "Cannot check if the sink's thingNodeId matches its id "
                "if the attribute 'id' is missing!"
            ) from e

        thing_node_id_from_id = str(id).rsplit(sep="_", maxsplit=1)[0]
        if thing_node_id_from_id != thingNodeId:
            raise ValueError(
                f"The sink's thing node id {thingNodeId} does not match its id {id}!"
            )
        return thingNodeId

    # pylint: disable=no-self-argument
    @validator("name")
    def name_matches_id(cls, name: str, values: dict) -> str:
        try:
            id = values["id"]  # pylint: disable=redefined-builtin
        except KeyError as e:
            raise ValueError(
                "Cannot check if the sink's name matches its id if the attribute 'id' is missing!"
            ) from e

        file_string_from_id = id.rsplit(sep="/", maxsplit=1)[1]
        thing_node_name_from_id = file_string_from_id.split("_",maxsplit=1)[0]
        
        if " - " not in name:
            raise ValueError()
        thing_node_name, sink_name_end = name.split(" - ")
        if thing_node_name != thing_node_name_from_id:
            raise ValueError(
                "The sink name must start with the name of the corresponding thing node!"
            )
        if sink_name_end != 'Next Trained Model':
            raise ValueError(
                "The sink name must end with 'Next Trained Model'!"
            )

        return name

    # pylint: disable=no-self-argument
    @validator("path")
    def path_matches_thing_node_id(cls, path: str, values: dict) -> str:
        try:
            thingNodeId = values["thingNodeId"]
        except KeyError as e:
            raise ValueError(
                "Cannot check if sink's path matches its thingNodeId "
                "if the attribute 'thingNodeId' is missing!"
            ) from e

        if path != thingNodeId:
            raise ValueError(
                f"The sink's path '{path}' must be the same string as its thingNodeId '{thingNodeId}'!"
            )

        return path

    # pylint: disable=no-self-argument
    @validator("metadataKey")
    def metadata_key_matches_name(cls, metadataKey: str, values: dict) -> str:
        try:
            name = values["name"]
        except KeyError as e:
            raise ValueError(
                "Cannot check if sink's metadataKey matches its name "
                "if the attribute 'name' is missing!"
            ) from e

        if metadataKey != name:
            raise ValueError(
                "The sink's metadataKey must be the same string as its name!"
            )

        return metadataKey

    @classmethod
    def from_thing_node(
        cls, thing_node: StructureThingNode
    ) -> "BlobStorageStructureSink":
        return BlobStorageStructureSink(
            id=thing_node.id + "_next",
            thingNodeId=thing_node.id,
            name=thing_node.name + " - " + "Next Trained Model",
            path=thing_node.id,
            metadataKey=thing_node.name + " - " + "Next Trained Model",
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
    identfier_separator: Literal[" - "] = " - "
    time_string_format: str = "%YY%mM%dD%Hh%Mm%Ss"
    sink_id_ending: str = "next"
    sink_name_ending: str = "Next Trained Model"

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
