import re
from datetime import datetime, timezone
from functools import cache, cached_property
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConstrainedStr, Field, ValidationError, validator

from hetdesrun.adapters.blob_storage import (
    BUCKET_NAME_DIR_SEPARATOR,
    GENERIC_SINK_ID_SUFFIX,
    GENERIC_SINK_NAME_SUFFIX,
    HIERARCHY_END_NODE_NAME_SEPARATOR,
    IDENTIFIER_SEPARATOR,
    OBJECT_KEY_DIR_SEPARATOR,
)
from hetdesrun.adapters.blob_storage.config import get_blob_adapter_config
from hetdesrun.adapters.blob_storage.exceptions import MissingHierarchyError


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
        r"^[a-zA-Z0-9:+\-"
        rf"{OBJECT_KEY_DIR_SEPARATOR}{IDENTIFIER_SEPARATOR}{BUCKET_NAME_DIR_SEPARATOR}]+$"
    )


class StructureBucket(BaseModel):
    name: BucketName

    class Config:
        frozen = True


def get_structure_bucket_and_object_key_prefix_from_id(
    id: IdString,  # noqa: A002
) -> tuple[StructureBucket, "IdString"]:
    if OBJECT_KEY_DIR_SEPARATOR not in id:
        raise ValueError(
            f"Cannot create bucket name and object key prefix based on an id {id} "
            f"which does not contain '{OBJECT_KEY_DIR_SEPARATOR}'."
        )

    bucket_name_string, object_key_string = id.split(
        OBJECT_KEY_DIR_SEPARATOR, maxsplit=1
    )

    try:
        bucket = StructureBucket(name=BucketName(bucket_name_string))
    except ValueError as e:
        raise ValueError(
            f"The first part '{bucket_name_string}' of the source id '{id}' "
            f"before the first '{OBJECT_KEY_DIR_SEPARATOR}' "
            "must correspond to a bucket name!\nBut it does not:\n" + str(e)
        ) from e
    return (
        bucket,
        IdString(object_key_string),
    )


class ObjectKey(BaseModel):
    string: IdString
    name: IdString
    time: datetime
    job_id: UUID

    @validator("time")
    def has_timezone_utc(cls, time: datetime) -> datetime:
        if time.tzinfo != timezone.utc:
            raise ValueError("The ObjectKey attribute time must have timezone UTC!")
        return time

    @classmethod
    def from_name_and_job_id(cls, name: IdString, job_id: UUID) -> "ObjectKey":
        now = datetime.now(timezone.utc).replace(microsecond=0)
        return ObjectKey(
            string=name
            + IDENTIFIER_SEPARATOR
            + now.isoformat()
            + IDENTIFIER_SEPARATOR
            + str(job_id),
            name=name,
            time=now,
            job_id=job_id,
        )

    @classmethod
    def from_name_and_time_and_job_id(
        cls, name: IdString, time: datetime, job_id: UUID
    ) -> "ObjectKey":
        return ObjectKey(
            string=name
            + IDENTIFIER_SEPARATOR
            + time.isoformat()
            + IDENTIFIER_SEPARATOR
            + str(job_id),
            name=name,
            time=time,
            job_id=job_id,
        )

    @classmethod
    def from_string(cls, string: IdString) -> "ObjectKey":
        try:
            name, time_string, job_id_string = string.rsplit(
                IDENTIFIER_SEPARATOR, maxsplit=2
            )
        except ValueError as e:
            raise ValueError(
                f"String '{string}' not a valid ObjectKey string, "
                f"because it contains '{IDENTIFIER_SEPARATOR}' less than twice!"
            ) from e
        return ObjectKey(
            string=string,
            name=name,
            time=datetime.fromisoformat(time_string).replace(tzinfo=timezone.utc),
            job_id=UUID(job_id_string),
        )

    @classmethod
    def from_thing_node_id_and_metadata_key(
        cls, thing_node_id: IdString, metadata_key: str
    ) -> "ObjectKey":
        if metadata_key.count(HIERARCHY_END_NODE_NAME_SEPARATOR) != 2:
            raise ValueError(
                f"Cannot create bucket name and object key based on a metadata key {metadata_key} "
                f"which does not contain '{HIERARCHY_END_NODE_NAME_SEPARATOR}' exactly twice."
            )
        name, time_string, job_id_string = metadata_key.split(
            HIERARCHY_END_NODE_NAME_SEPARATOR
        )

        if not thing_node_id.endswith(name):
            raise ValueError(
                f"Thing node id '{thing_node_id}' and metadata key '{metadata_key}' do not match."
            )

        _, object_key_prefix = get_structure_bucket_and_object_key_prefix_from_id(
            thing_node_id
        )

        return ObjectKey.from_name_and_time_and_job_id(
            name=object_key_prefix,
            time=datetime.fromisoformat(time_string).replace(tzinfo=timezone.utc),
            job_id=UUID(job_id_string),
        )

    def to_thing_node_id(self, bucket: StructureBucket) -> IdString:
        return IdString(bucket.name + OBJECT_KEY_DIR_SEPARATOR + self.name)


class InfoResponse(BaseModel):
    id: str  # noqa: A003
    name: str
    version: str


class StructureThingNode(BaseModel):
    id: IdString  # noqa: A003
    parentId: IdString | None = None
    name: ThingNodeName
    description: str

    @validator("name")
    def id_consists_of_parent_id_and_name(
        cls, name: ThingNodeName, values: dict
    ) -> ThingNodeName:
        try:
            id = values["id"]  # noqa: A001
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
                f"connected by one of the separators '{BUCKET_NAME_DIR_SEPARATOR}' or "
                f"'{OBJECT_KEY_DIR_SEPARATOR}' with its name '{name}'!"
            )
        return name


class BlobStorageStructureSource(BaseModel):
    id: IdString  # noqa: A003
    thingNodeId: IdString
    name: str
    path: str = Field(..., description="Display path used in Designer Frontend")
    metadataKey: str
    type: Literal["metadata(any)"] = "metadata(any)"  # noqa: A003
    visible: Literal[True] = True
    filters: dict[str, dict] | None = {}

    @validator("id")
    def id_matches_scheme(cls, id: IdString) -> IdString:  # noqa: A002
        _, object_key_string = get_structure_bucket_and_object_key_prefix_from_id(id)
        try:
            ObjectKey.from_string(IdString(object_key_string))
        except ValueError as e:
            raise ValueError(
                f"The second part '{object_key_string}' of the source id '{id}' after the first "
                "'/' must correspond to an object key string!\nBut it does not:\n"
                + str(e)
            ) from e
        return id

    @validator("thingNodeId")
    def thing_node_id_matches_id(cls, thingNodeId: IdString, values: dict) -> IdString:
        try:
            id = values["id"]  # noqa: A001
        except KeyError as e:
            raise ValueError(
                f"Cannot check if the source's thingNodeId '{thingNodeId}' matches its id "
                "if the attribute 'id' is missing!"
            ) from e

        thing_node_id_from_id = str(id).rsplit(sep=IDENTIFIER_SEPARATOR, maxsplit=2)[0]
        if thing_node_id_from_id != thingNodeId:
            raise ValueError(
                f"The source's thing node id '{thingNodeId}' does not match its id '{id}'!"
            )
        return thingNodeId

    @validator("name")
    def name_matches_id(cls, name: str, values: dict) -> str:
        try:
            id = values["id"]  # noqa: A001
        except KeyError as e:
            raise ValueError(
                f"Cannot check if the source's name '{name}' matches its id "
                "if the attribute 'id' is missing!"
            ) from e
        file_string_from_id = id.rsplit(sep=OBJECT_KEY_DIR_SEPARATOR, maxsplit=1)[1]
        file_ok = ObjectKey.from_string(IdString(file_string_from_id))
        if name.count(HIERARCHY_END_NODE_NAME_SEPARATOR) != 2:
            raise ValueError(
                f"The source name '{name}' must contain "
                f"the string '{HIERARCHY_END_NODE_NAME_SEPARATOR}' exactly twice!"
            )
        thing_node_name, source_time, job_id = name.split(
            HIERARCHY_END_NODE_NAME_SEPARATOR
        )
        if thing_node_name != file_ok.name:
            raise ValueError(
                f"The source name '{name}' must start with the name '{file_ok.name}' "
                "of the corresponding thing node!"
            )
        if file_ok.time.astimezone(timezone.utc).isoformat(sep=" ") != source_time:
            raise ValueError(
                f"The time of the source's name '{name}' must match to the time in its id '{id}'!"
            )

        if not str(file_ok.job_id) == job_id:
            raise ValueError(
                f"The job id '{job_id}' of the source's name '{name}' "
                f"must match to the job id '{file_ok.job_id}' in its id '{id}'!"
            )

        return name

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

    @validator("metadataKey")
    def metadata_key_matches_name(cls, metadataKey: str, values: dict) -> str:
        try:
            name = values["name"]
        except KeyError as e:
            raise ValueError(
                f"Cannot check if source's metadataKey '{metadataKey}' matches its name "
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
            object_key.name.rsplit(sep=OBJECT_KEY_DIR_SEPARATOR, maxsplit=1)[-1]
            + HIERARCHY_END_NODE_NAME_SEPARATOR
            + object_key.time.astimezone(timezone.utc).isoformat(sep=" ")
            + HIERARCHY_END_NODE_NAME_SEPARATOR
            + str(object_key.job_id)
        )
        thing_node_id = object_key.to_thing_node_id(bucket)
        return BlobStorageStructureSource(
            id=bucket.name + OBJECT_KEY_DIR_SEPARATOR + object_key.string,
            thingNodeId=thing_node_id,
            name=name,
            path=thing_node_id,
            metadataKey=name,
        )


class MultipleSourcesResponse(BaseModel):
    resultCount: int
    sources: list[BlobStorageStructureSource]


class BlobStorageStructureSink(BaseModel):
    id: IdString  # noqa: A003
    thingNodeId: IdString
    name: str
    path: str = Field(..., description="Display path used in Designer Frontend")
    metadataKey: str
    type: Literal["metadata(any)"] = "metadata(any)"  # noqa: A003
    visible: Literal[True] = True
    filters: dict[str, dict] | None = {}

    @validator("id")
    def id_matches_scheme(cls, id: IdString) -> IdString:  # noqa: A002
        bucket, _ = get_structure_bucket_and_object_key_prefix_from_id(id)

        if not id.endswith(IDENTIFIER_SEPARATOR + GENERIC_SINK_ID_SUFFIX):
            raise ValueError(
                f"The sink id '{id}' must end with '{IDENTIFIER_SEPARATOR+GENERIC_SINK_ID_SUFFIX}'!"
            )
        return id

    @validator("thingNodeId")
    def thing_node_id_matches_id(cls, thingNodeId: IdString, values: dict) -> IdString:
        try:
            id = values["id"]  # noqa: A001
        except KeyError as e:
            raise ValueError(
                f"Cannot check if the sink's thingNodeId '{thingNodeId}' matches its id "
                "if the attribute 'id' is missing!"
            ) from e

        thing_node_id_from_id = str(id).rsplit(
            sep=IDENTIFIER_SEPARATOR + GENERIC_SINK_ID_SUFFIX, maxsplit=1
        )[0]
        if thing_node_id_from_id != thingNodeId:
            raise ValueError(
                f"The sink's thing node id '{thingNodeId}' does not match its id '{id}'!"
            )
        return thingNodeId

    @validator("name")
    def name_matches_id(cls, name: str, values: dict) -> str:
        try:
            id = values["id"]  # noqa: A001
        except KeyError as e:
            raise ValueError(
                f"Cannot check if the sink's name '{name}' matches its id if the attribute 'id' "
                "is missing!"
            ) from e

        file_string_from_id = id.rsplit(sep=OBJECT_KEY_DIR_SEPARATOR, maxsplit=1)[1]
        thing_node_name_from_id = file_string_from_id.split(
            IDENTIFIER_SEPARATOR, maxsplit=1
        )[0]

        if HIERARCHY_END_NODE_NAME_SEPARATOR not in name:
            raise ValueError(
                f"The sink name '{name}' must contain "
                f"the string '{HIERARCHY_END_NODE_NAME_SEPARATOR}'!"
            )
        thing_node_name, sink_name_end = name.split(HIERARCHY_END_NODE_NAME_SEPARATOR)
        if thing_node_name != thing_node_name_from_id:
            raise ValueError(
                f"The sink name '{name}' must start with the name '{thing_node_name_from_id}' "
                "of the corresponding thing node!"
            )
        if sink_name_end != GENERIC_SINK_NAME_SUFFIX:
            raise ValueError(
                f"The sink name '{name}' must end with '{GENERIC_SINK_NAME_SUFFIX}'!"
            )

        return name

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
            id=thing_node.id + IDENTIFIER_SEPARATOR + GENERIC_SINK_ID_SUFFIX,
            thingNodeId=thing_node.id,
            name=thing_node.name
            + HIERARCHY_END_NODE_NAME_SEPARATOR
            + GENERIC_SINK_NAME_SUFFIX,
            path=thing_node.id,
            metadataKey=thing_node.name
            + HIERARCHY_END_NODE_NAME_SEPARATOR
            + GENERIC_SINK_NAME_SUFFIX,
        )

    def to_structure_bucket_and_object_key(
        self, job_id: UUID
    ) -> tuple[StructureBucket, ObjectKey]:
        (
            bucket,
            object_key_name,
        ) = get_structure_bucket_and_object_key_prefix_from_id(self.thingNodeId)
        return bucket, ObjectKey.from_name_and_job_id(IdString(object_key_name), job_id)


class MultipleSinksResponse(BaseModel):
    resultCount: int
    sinks: list[BlobStorageStructureSink]


class StructureResponse(BaseModel):
    id: str  # noqa: A003
    name: str
    thingNodes: list[StructureThingNode]
    sources: list[BlobStorageStructureSource]
    sinks: list[BlobStorageStructureSink]


class HierarchyNode(BaseModel):
    name: ThingNodeName
    description: str
    substructure: tuple["HierarchyNode", ...] | None = None
    below_structure_defines_object_key: bool = False

    class Config:
        frozen = True  # __setattr__ not allowed and a __hash__ method for the class is generated

    def get_depth(self) -> int:
        depth = 1
        if self.substructure is not None and len(self.substructure) != 0:
            depths: list[int] = []
            for hierarchy_node in self.substructure:
                depths.append(hierarchy_node.get_depth())
            depth = depth + max(depths)
        return depth

    def to_thing_node(
        self, parent_id: IdString | None, separator: Literal["-", "/"]
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
        thing_nodes: list[StructureThingNode],
        buckets: list[StructureBucket],
        sinks: list[BlobStorageStructureSink],
        parent_id: IdString | None,
        part_of_bucket_name: bool,
    ) -> None:
        if part_of_bucket_name is True and (
            self.substructure is None or len(self.substructure) == 0
        ):
            raise ValueError(
                f"Hierarchy Error identified at HierarchyNode '{self.name}' which appears to be "
                "part of a bucket name but does not contain a substructure! "
                "Without an object key prefix no sinks or sources can be generated!"
            )

        thing_node = self.to_thing_node(
            parent_id,
            separator=BUCKET_NAME_DIR_SEPARATOR
            if part_of_bucket_name
            else OBJECT_KEY_DIR_SEPARATOR,
        )
        thing_nodes.append(thing_node)

        below_structure_defines_object_key = (
            self.below_structure_defines_object_key is True
            or (part_of_bucket_name is True and self.get_depth() == 2)
        )
        if below_structure_defines_object_key:
            if part_of_bucket_name is False:
                raise ValueError(
                    f"Hierarchy Error identified at HierarchyNode '{self.name}'! It appears as if "
                    '"below_structure_defines_object_key" has been true for a parent HierarchyNode '
                    "already, but then it should not be true again for any of its subcategories!"
                )
            try:
                bucket = StructureBucket(name=thing_node.id)
            except ValidationError as error:
                raise ValueError(
                    f"Validation Error for transformation of StructureThingNode "
                    f"{thing_node.id} to BucketName for HierarchyNode '{self.name}':\n{error}"
                ) from error
            else:
                buckets.append(bucket)

        if self.substructure is not None and len(self.substructure) != 0:
            for hierarchy_node in self.substructure:
                hierarchy_node.create_structure(
                    thing_nodes=thing_nodes,
                    buckets=buckets,
                    sinks=sinks,
                    parent_id=thing_node.id,
                    part_of_bucket_name=part_of_bucket_name
                    if below_structure_defines_object_key is False
                    else False,
                )
        else:  # hierarchy_node.substructure is None or len(hierarchy_node.substructure) == 0
            sink = BlobStorageStructureSink.from_thing_node(thing_node)
            sinks.append(sink)


def find_duplicates(item_list: list) -> list:
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
    structure: tuple[HierarchyNode, ...]
) -> tuple[
    list[StructureThingNode], list[StructureBucket], list[BlobStorageStructureSink]
]:
    thing_nodes: list[StructureThingNode] = []
    bucket_names: list[StructureBucket] = []
    sinks: list[BlobStorageStructureSink] = []
    for hierarchy_node in structure:
        hierarchy_node.create_structure(
            thing_nodes, bucket_names, sinks, parent_id=None, part_of_bucket_name=True
        )

    if len(bucket_names) != len(set(bucket_names)):
        bucket_names_string = ", ".join(bn.name for bn in bucket_names)
        raise ValueError(f"Bucket names are not unique!\n{bucket_names_string}")

    thing_node_ids = [tn.id for tn in thing_nodes]
    if len(thing_nodes) != len(set(thing_node_ids)):
        thing_nodes_string = ", ".join(thing_node_ids)
        raise ValueError(f"Thing nodes are not unique!\n{thing_nodes_string}")

    # The sinks are unique if the thing nodes are unique.

    return thing_nodes, bucket_names, sinks


class AdapterHierarchy(BaseModel):
    """Define the Blob Storage Hierarchy.

    The Amazon S3 data model is a flat structure: You can create buckets and store objects in them.
    There is no hierarchy of subbuckets or subfolders. However, the hierarchy of the adapter is
    transferred to the bucket names and object keys by using key name prefixes and delimiters.
    The Amazon S3 console and the AWS SDKs can infer hierarchy from object keys with such prefixes
    and delimiters and introduce the concept of folders.
    """

    structure: tuple[HierarchyNode, ...]

    class Config:
        arbitrary_types_allowed = True
        keep_untouched = (
            cached_property,
        )  # cached_property currently not supported by pydantic
        # https://github.com/pydantic/pydantic/issues/1241
        frozen = True  # __setattr__ not allowed and a __hash__ method for the class is generated

    @cached_property
    def create_structure(
        self,
    ) -> tuple[
        list[StructureThingNode], list[StructureBucket], list[BlobStorageStructureSink]
    ]:
        return create_blob_storage_adapter_structure_objects_from_hierarchy(
            structure=self.structure
        )

    @cached_property
    def thing_nodes(self) -> list[StructureThingNode]:
        thing_nodes, _, _ = self.create_structure
        return thing_nodes

    @cached_property
    def thing_node_by_id(self) -> dict[IdString, StructureThingNode]:
        return {tn.id: tn for tn in self.thing_nodes}

    @cached_property
    def thing_nodes_by_parent_id(
        self,
    ) -> dict[IdString | None, list[StructureThingNode]]:
        tn_dict: dict[IdString | None, list[StructureThingNode]] = {}
        for tn in self.thing_nodes:
            if tn.parentId in tn_dict:
                tn_dict[tn.parentId].append(tn)
            else:
                tn_dict[tn.parentId] = [tn]
        return tn_dict

    @cached_property
    def structure_buckets(self) -> list[StructureBucket]:
        _, buckets, _ = self.create_structure
        if len(buckets) != len(set(buckets)):
            msg = (
                "The bucket names generated from the config file are not unique!\n"
                "They contain the following duplicates: "
                + ", ".join(duplicate.name for duplicate in find_duplicates(buckets))
            )
            raise ValueError(msg)
        return buckets

    @cached_property
    def sinks(self) -> list[BlobStorageStructureSink]:
        _, _, sinks = self.create_structure
        return sinks

    @cached_property
    def sink_by_id(self) -> dict[IdString, BlobStorageStructureSink]:
        return {snk.id: snk for snk in self.sinks}

    @cached_property
    def sinks_by_parent_id(self) -> dict[IdString, list[BlobStorageStructureSink]]:
        snk_dict: dict[IdString, list[BlobStorageStructureSink]] = {}
        for snk in self.sinks:
            if snk.thingNodeId in snk_dict:
                snk_dict[snk.thingNodeId].append(snk)
            else:
                snk_dict[snk.thingNodeId] = [snk]
        return snk_dict

    @cached_property
    def sink_by_thing_node_id_and_metadata_key(
        self,
    ) -> dict[tuple[IdString, str], BlobStorageStructureSink]:
        return {(snk.thingNodeId, snk.metadataKey): snk for snk in self.sinks}

    @classmethod
    def from_file(
        cls,
        path: str = get_blob_adapter_config().adapter_hierarchy_location,
    ) -> "AdapterHierarchy":
        try:
            return AdapterHierarchy.parse_file(path)
        except FileNotFoundError as error:
            raise MissingHierarchyError(
                f"Could not find hierarchy json file at path '{path}':\n{str(error)}"
            ) from error


@cache
def get_adapter_structure() -> AdapterHierarchy:
    """Get adapter structure.

    A MissingHierarchyError raised from the AdapterHierarchy method from_file may occur.
    """
    return AdapterHierarchy.from_file()
