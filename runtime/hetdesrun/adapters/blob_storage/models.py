import re
from datetime import datetime, timezone
from functools import cache, cached_property
from typing import Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, ConstrainedStr, Field, ValidationError, validator

from hetdesrun.adapters.blob_storage import (
    BUCKET_NAME_DIR_SEPARATOR,
    IDENTIFIER_SEPARATOR,
    LEAF_NAME_SEPARATOR,
    OBJECT_KEY_DIR_SEPARATOR,
    SINK_ID_ENDING,
    SINK_NAME_ENDING,
)
from hetdesrun.adapters.blob_storage.config import get_blob_adapter_config
from hetdesrun.adapters.blob_storage.exceptions import (
    BucketNameInvalidError,
    HierarchyError,
    MissingHierarchyError,
)


class ThingNodeName(ConstrainedStr):
    min_length = 1
    max_length = 63
    regex = re.compile(r"^[a-zA-Z0-9]+$")


class BucketName(ConstrainedStr):
    min_length = 3
    max_length = 63
    regex = re.compile(rf"^[a-z0-9{BUCKET_NAME_DIR_SEPARATOR}]+$")


class IdString(ConstrainedStr):
    min_length = 1
    regex = re.compile(
        (
            r"^[a-zA-Z0-9:+\-"
            rf"{OBJECT_KEY_DIR_SEPARATOR}{IDENTIFIER_SEPARATOR}{BUCKET_NAME_DIR_SEPARATOR}]+$"
        )
    )


class StructureBucket(BaseModel):
    name: BucketName

    class Config:
        frozen = True


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
            string=name + IDENTIFIER_SEPARATOR + now.isoformat(),
            name=name,
            time=now,
        )

    @classmethod
    def from_string(cls, string: IdString) -> "ObjectKey":
        try:
            name, timestring = string.rsplit(IDENTIFIER_SEPARATOR, maxsplit=1)
        except ValueError as e:
            raise ValueError(
                f"String {string} not a valid ObjectKey string, "
                f"because it contains no '{IDENTIFIER_SEPARATOR}'!"
            ) from e
        return ObjectKey(
            string=string,
            name=name,
            time=datetime.fromisoformat(timestring).replace(tzinfo=timezone.utc),
        )

    def to_thing_node_id(self, bucket: StructureBucket) -> IdString:
        return IdString(bucket.name + OBJECT_KEY_DIR_SEPARATOR + self.name)


class InfoResponse(BaseModel):
    id: str
    name: str
    version: str


class StructureThingNode(BaseModel):
    id: IdString
    parentId: Optional[IdString] = None
    name: ThingNodeName
    description: str

    # pylint: disable=no-self-argument
    @validator("name")
    def id_consists_of_parent_id_and_name(
        cls, name: ThingNodeName, values: dict
    ) -> ThingNodeName:
        try:
            id = values["id"]  # pylint: disable=redefined-builtin
            parent_id = values["parentId"]
        except KeyError as e:
            raise ValueError(
                f"Cannot check if id consists of parent id and lowered name '{name}' "
                "if the attribute 'id' is missing!"
            ) from e

        if id not in (
            (parent_id + separator if parent_id is not None else "")
            + (str(name).lower() if separator == BUCKET_NAME_DIR_SEPARATOR else name)
            for separator in (BUCKET_NAME_DIR_SEPARATOR, OBJECT_KEY_DIR_SEPARATOR)
        ):
            raise ValueError(
                f"The id '{id}' of a thing node must consist of its parent id '{parent_id}' "
                f"connected by one of the separators {BUCKET_NAME_DIR_SEPARATOR} or "
                f"{OBJECT_KEY_DIR_SEPARATOR} with its name '{name}'!"
            )
        return name


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
    def id_matches_scheme(
        cls, id: IdString  # pylint: disable=redefined-builtin
    ) -> IdString:
        if OBJECT_KEY_DIR_SEPARATOR not in id:
            raise ValueError(
                f"The source id '{id}' must contain at least one '{OBJECT_KEY_DIR_SEPARATOR}'!"
            )
        bucket_name, object_key_string = id.split(sep="/", maxsplit=1)
        try:
            StructureBucket(name=bucket_name)
        except ValidationError as e:
            raise ValueError(
                f"The first part '{bucket_name}' of the source id '{id}' "
                f"before the first '{OBJECT_KEY_DIR_SEPARATOR}' "
                "must correspond to a bucket name!\nBut it does not:\n" + str(e)
            ) from e

        try:
            ObjectKey.from_string(IdString(object_key_string))
        except ValueError as e:
            raise ValueError(
                f"The second part '{object_key_string}' of the source id '{id}' after the first "
                "'/' must correspond to an object key string!\nBut it does not:\n"
                + str(e)
            ) from e
        return id

    # pylint: disable=no-self-argument
    @validator("thingNodeId")
    def thing_node_id_matches_id(cls, thingNodeId: IdString, values: dict) -> IdString:
        try:
            id = values["id"]  # pylint: disable=redefined-builtin
        except KeyError as e:
            raise ValueError(
                f"Cannot check if the source's thingNodeId '{thingNodeId}' matches its id "
                "if the attribute 'id' is missing!"
            ) from e

        thing_node_id_from_id = str(id).rsplit(sep=IDENTIFIER_SEPARATOR, maxsplit=1)[0]
        if thing_node_id_from_id != thingNodeId:
            raise ValueError(
                f"The source's thing node id '{thingNodeId}' does not match its id '{id}'!"
            )
        return thingNodeId

    # pylint: disable=no-self-argument
    @validator("name")
    def name_matches_id(cls, name: str, values: dict) -> str:
        try:
            id = values["id"]  # pylint: disable=redefined-builtin
        except KeyError as e:
            raise ValueError(
                f"Cannot check if the source's name '{name}' matches its id "
                "if the attribute 'id' is missing!"
            ) from e
        file_string_from_id = id.rsplit(sep=OBJECT_KEY_DIR_SEPARATOR, maxsplit=1)[1]
        file_ok = ObjectKey.from_string(IdString(file_string_from_id))
        if LEAF_NAME_SEPARATOR not in name:
            raise ValueError(
                f"The source name '{name}' must contain the string '{LEAF_NAME_SEPARATOR}'!"
            )
        thing_node_name, source_time = name.split(LEAF_NAME_SEPARATOR)
        if thing_node_name != file_ok.name:
            raise ValueError(
                f"The source name '{name}' must start with the name '{file_ok.name}' "
                "of the corresponding thing node!"
            )
        if file_ok.time.astimezone(timezone.utc).isoformat(sep=" ") != source_time:
            raise ValueError(
                f"The time of the source's name '{name}' must match to the time in its id '{id}'!"
            )

        return name

    # pylint: disable=no-self-argument
    @validator("path")
    def path_matches_thing_node_id(cls, path: str, values: dict) -> str:
        try:
            thingNodeId = values["thingNodeId"]
        except KeyError as e:
            raise ValueError(
                f"Cannot check if source's path '{path}' matches its thingNodeId "
                "if the attribute 'thingNodeId' is missing!"
            ) from e

        if path != thingNodeId:
            raise ValueError(
                f"The source path '{path}' must be the same string as "
                f"its thingNodeId '{thingNodeId}'!"
            )

        return path

    # pylint: disable=no-self-argument
    @validator("metadataKey")
    def metadata_key_matches_name(cls, metadataKey: str, values: dict) -> str:
        try:
            name = values["name"]
        except KeyError as e:
            raise ValueError(
                f"Cannot check if source's metadataKey {metadataKey} matches its name "
                "if the attribute 'name' is missing!"
            ) from e

        if metadataKey != name:
            raise ValueError(
                f"The source's metadataKey '{metadataKey}' must be the same string as "
                f"its name '{name}'!"
            )

        return metadataKey

    @classmethod
    def from_structure_bucket_and_object_key(
        cls, bucket: StructureBucket, object_key: ObjectKey
    ) -> "BlobStorageStructureSource":
        name = (
            object_key.name
            + LEAF_NAME_SEPARATOR
            + object_key.time.astimezone(timezone.utc).isoformat(sep=" ")
        )
        thing_node_id = object_key.to_thing_node_id(bucket)
        return BlobStorageStructureSource(
            id=bucket.name + OBJECT_KEY_DIR_SEPARATOR + object_key.string,
            thingNodeId=thing_node_id,
            name=name,
            path=thing_node_id,
            metadataKey=name,
        )

    def to_structure_bucket_and_object_key(self) -> Tuple[StructureBucket, ObjectKey]:
        bucket_name_string, object_key_string = self.id.split(
            sep=OBJECT_KEY_DIR_SEPARATOR, maxsplit=1
        )
        return StructureBucket(name=bucket_name_string), ObjectKey.from_string(
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
    def id_matches_scheme(
        cls, id: IdString  # pylint: disable=redefined-builtin
    ) -> IdString:
        if OBJECT_KEY_DIR_SEPARATOR not in id:
            raise ValueError(
                f"The sink id '{id}' must contain at least one '{OBJECT_KEY_DIR_SEPARATOR}'!"
            )
        bucket_name_string = id.split(sep=OBJECT_KEY_DIR_SEPARATOR, maxsplit=1)[0]
        try:
            StructureBucket(name=bucket_name_string)
        except ValidationError as e:
            raise ValueError(
                f"The first part '{bucket_name_string}' of the sink id '{id}' "
                f"before the first '{OBJECT_KEY_DIR_SEPARATOR}' must "
                "correspond to a bucket name!\nBut it does not:\n" + str(e)
            ) from e

        if not id.endswith(IDENTIFIER_SEPARATOR + SINK_ID_ENDING):
            raise ValueError(
                f"The sink id '{id}' must end with '{IDENTIFIER_SEPARATOR+SINK_ID_ENDING}'!"
            )
        return id

    # pylint: disable=no-self-argument
    @validator("thingNodeId")
    def thing_node_id_matches_id(cls, thingNodeId: IdString, values: dict) -> IdString:
        try:
            id = values["id"]  # pylint: disable=redefined-builtin
        except KeyError as e:
            raise ValueError(
                f"Cannot check if the sink's thingNodeId '{thingNodeId}' matches its id "
                "if the attribute 'id' is missing!"
            ) from e

        thing_node_id_from_id = str(id).rsplit(sep="_", maxsplit=1)[0]
        if thing_node_id_from_id != thingNodeId:
            raise ValueError(
                f"The sink's thing node id '{thingNodeId}' does not match its id '{id}'!"
            )
        return thingNodeId

    # pylint: disable=no-self-argument
    @validator("name")
    def name_matches_id(cls, name: str, values: dict) -> str:
        try:
            id = values["id"]  # pylint: disable=redefined-builtin
        except KeyError as e:
            raise ValueError(
                f"Cannot check if the sink's name '{name}' matches its id if the attribute 'id' "
                "is missing!"
            ) from e

        file_string_from_id = id.rsplit(sep=OBJECT_KEY_DIR_SEPARATOR, maxsplit=1)[1]
        thing_node_name_from_id = file_string_from_id.split(
            IDENTIFIER_SEPARATOR, maxsplit=1
        )[0]

        if LEAF_NAME_SEPARATOR not in name:
            raise ValueError(
                f"The sink name '{name}' must contain the string '{LEAF_NAME_SEPARATOR}'!"
            )
        thing_node_name, sink_name_end = name.split(LEAF_NAME_SEPARATOR)
        if thing_node_name != thing_node_name_from_id:
            raise ValueError(
                f"The sink name '{name}' must start with the name '{thing_node_name_from_id}' "
                "of the corresponding thing node!"
            )
        if sink_name_end != SINK_NAME_ENDING:
            raise ValueError(
                f"The sink name '{name}' must end with '{SINK_NAME_ENDING}'!"
            )

        return name

    # pylint: disable=no-self-argument
    @validator("path")
    def path_matches_thing_node_id(cls, path: str, values: dict) -> str:
        try:
            thingNodeId = values["thingNodeId"]
        except KeyError as e:
            raise ValueError(
                f"Cannot check if sink's path '{path}' matches its thingNodeId "
                "if the attribute 'thingNodeId' is missing!"
            ) from e

        if path != thingNodeId:
            raise ValueError(
                f"The sink's path '{path}' must be the same string as "
                f"its thingNodeId '{thingNodeId}'!"
            )

        return path

    # pylint: disable=no-self-argument
    @validator("metadataKey")
    def metadata_key_matches_name(cls, metadataKey: str, values: dict) -> str:
        try:
            name = values["name"]
        except KeyError as e:
            raise ValueError(
                f"Cannot check if sink's metadataKey '{metadataKey}' matches its name "
                "if the attribute 'name' is missing!"
            ) from e

        if metadataKey != name:
            raise ValueError(
                f"The sink's metadataKey '{metadataKey}' must be the same string as "
                f"its name '{name}'!"
            )

        return metadataKey

    @classmethod
    def from_thing_node(
        cls, thing_node: StructureThingNode
    ) -> "BlobStorageStructureSink":
        return BlobStorageStructureSink(
            id=thing_node.id + IDENTIFIER_SEPARATOR + SINK_ID_ENDING,
            thingNodeId=thing_node.id,
            name=thing_node.name + LEAF_NAME_SEPARATOR + SINK_NAME_ENDING,
            path=thing_node.id,
            metadataKey=thing_node.name + LEAF_NAME_SEPARATOR + SINK_NAME_ENDING,
        )

    def to_structure_bucket_and_object_key(self) -> Tuple[StructureBucket, ObjectKey]:
        bucket_name_string, object_key_name = self.thingNodeId.split(
            sep=OBJECT_KEY_DIR_SEPARATOR, maxsplit=1
        )
        return StructureBucket(name=bucket_name_string), ObjectKey.from_name(
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
    substructure: Optional[Tuple["Category", ...]] = None

    class Config:
        frozen = True  # __setattr__ not allowed and a __hash__ method for the class is generated

    def get_depth(self) -> int:
        depth = 1
        if self.substructure is not None and len(self.substructure) != 0:
            depths: List[int] = []
            # pylint: disable=not-an-iterable
            for category in self.substructure:
                depths.append(category.get_depth())
            depth = depth + max(depths)
        return depth

    def to_thing_node(
        self, parent_id: Optional[IdString], separator: Literal["-", "/"]
    ) -> StructureThingNode:
        return StructureThingNode(
            id=(parent_id + separator if parent_id is not None else "")
            + (
                self.name.lower()
                if separator == BUCKET_NAME_DIR_SEPARATOR
                else self.name
            ),
            parentId=parent_id,
            name=self.name,
            description=self.description,
        )

    def create_structure(
        self,
        thing_nodes: List[StructureThingNode],
        buckets: List[StructureBucket],
        sinks: List[BlobStorageStructureSink],
        object_key_depth: int,
        parent_id: Optional[IdString],
    ) -> None:
        thing_node = self.to_thing_node(
            parent_id,
            separator=BUCKET_NAME_DIR_SEPARATOR
            if self.get_depth() > object_key_depth
            else OBJECT_KEY_DIR_SEPARATOR,
        )
        thing_nodes.append(thing_node)

        if self.get_depth() == object_key_depth + 1:
            try:
                buckets.append(StructureBucket(name=thing_node.id))
            except ValidationError as error:
                raise BucketNameInvalidError(
                    f"Validation Error for transformation of StructureThingNode "
                    f"{thing_node.id} to BucketName:\n{error}"
                ) from error

        if self.substructure is not None and len(self.substructure) != 0:
            # pylint: disable=not-an-iterable
            for category in self.substructure:
                category.create_structure(
                    thing_nodes, buckets, sinks, object_key_depth, thing_node.id
                )
        else:  # category.substructure is None or len(category.substructure) == 0
            sink = BlobStorageStructureSink.from_thing_node(thing_node)
            sinks.append(sink)


def find_duplicates(item_list: List) -> List:
    seen = set()
    duplicates = []
    for item in item_list:
        if item in seen:
            duplicates.append(item)
        else:
            seen.add(item)
    return duplicates


@cache
def create_blob_storage_adapter_structure_objects_from_hierarchy(
    object_key_depth: int, structure: Tuple[Category, ...]
) -> Tuple[
    List[StructureThingNode], List[StructureBucket], List[BlobStorageStructureSink]
]:
    thing_nodes: List[StructureThingNode] = []
    bucket_names: List[StructureBucket] = []
    sinks: List[BlobStorageStructureSink] = []
    for category in structure:
        category.create_structure(
            thing_nodes, bucket_names, sinks, object_key_depth, parent_id=None
        )
    return thing_nodes, bucket_names, sinks


class AdapterHierarchy(BaseModel):
    """Define the Blob Storage Hierarchy.

    The Amazon S3 data model is a flat structure: You can create buckets and store objects in them.
    There is no hierarchy of subbuckets or subfolders. However, the hierarchy of the adapter is
    transferred to the bucket names and object keys by using key name prefixes and delimiters.
    The Amazon S3 console and the AWS SDKs can infer hierarchy from object keys with such prefixes
    and delimiters and introduce the concept of folders.
    """

    structure: Tuple[Category, ...]
    object_key_depth: int

    class Config:
        arbitrary_types_allowed = True
        keep_untouched = (
            cached_property,
        )  # cached_property currently not supported by pydantic
        # https://github.com/pydantic/pydantic/issues/1241
        frozen = True  # __setattr__ not allowed and a __hash__ method for the class is generated

    # pylint: disable=no-self-argument
    @validator("object_key_depth")
    def structure_deeper_than_object_key_depth(
        cls, object_key_depth: int, values: dict
    ) -> int:
        try:
            structure: List[Category] = values["structure"]
        except KeyError as e:
            raise ValueError(
                "Cannot check if structure is deeper than the object key depth "
                f"'{object_key_depth}' if the attribute 'structure' is missing!"
            ) from e

        depths: List[int] = []
        for category in structure:
            depths.append(category.get_depth())

        if not min(depths) > object_key_depth:
            raise HierarchyError(
                "Each branch of the structure must be deeper than "
                f"the object key depth '{object_key_depth}'!"
            )

        values["structure"] = structure
        return object_key_depth

    def create_structure(
        self,
    ) -> Tuple[
        List[StructureThingNode], List[StructureBucket], List[BlobStorageStructureSink]
    ]:
        return create_blob_storage_adapter_structure_objects_from_hierarchy(
            object_key_depth=self.object_key_depth, structure=self.structure
        )

    @cached_property
    def thing_nodes(self) -> List[StructureThingNode]:
        thing_nodes, _, _ = self.create_structure()
        return thing_nodes

    @cached_property
    def structure_buckets(self) -> List[StructureBucket]:
        _, buckets, _ = self.create_structure()
        if len(buckets) != len(set(buckets)):
            msg = (
                "The bucket names generated from the config file are not unique!\n"
                "They contain the following duplicates: "
                + ", ".join(duplicate.name for duplicate in find_duplicates(buckets))
            )
            raise HierarchyError(msg)
        return buckets

    @cached_property
    def sinks(self) -> List[BlobStorageStructureSink]:
        _, _, sinks = self.create_structure()
        return sinks

    @classmethod
    def from_file(
        cls,
        path: str = get_blob_adapter_config().adapter_hierarchy_location,
    ) -> "AdapterHierarchy":
        try:
            return AdapterHierarchy.parse_file(path)
        except FileNotFoundError as error:
            raise MissingHierarchyError(
                f"Could not find hierarchy json file at path {path}:\n{str(error)}"
            ) from error


@cache
def get_adapter_structure() -> AdapterHierarchy:
    return AdapterHierarchy.from_file()
