import uuid
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, ValidationError, root_validator, validator

from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.persistence.structure_service_dbmodels import (
    ElementTypeOrm,
    SinkOrm,
    SourceOrm,
    ThingNodeOrm,
)
from hetdesrun.structure.db.exceptions import DBIntegrityError


class ElementType(BaseModel):
    id: UUID = Field(
        default_factory=uuid.uuid4,
        description="The primary key for the ElementType table",
    )
    external_id: str = Field(..., description="Externally provided unique identifier")
    stakeholder_key: str = Field(..., description="Stakeholder key for the ElementType")
    name: str = Field(..., description="Unique name of the ElementType")
    description: str | None = Field(None, description="Description of the ElementType")
    thing_nodes: list["ThingNode"] = Field(
        default_factory=list, description="List of associated ThingNodes"
    )

    class Config:
        orm_mode = True

    def to_orm_model(self) -> ElementTypeOrm:
        return ElementTypeOrm(
            id=self.id,
            external_id=self.external_id,
            stakeholder_key=self.stakeholder_key,
            name=self.name,
            description=self.description,
            thing_nodes=[tn.to_orm_model() for tn in self.thing_nodes],
        )

    @classmethod
    def from_orm_model(cls, orm_model: ElementTypeOrm) -> "ElementType":
        try:
            return cls(
                id=orm_model.id,
                external_id=orm_model.external_id,
                stakeholder_key=orm_model.stakeholder_key,
                name=orm_model.name,
                description=orm_model.description,
            )
        except ValidationError as e:
            msg = (
                f"Could not validate db entry for id {orm_model.id}. "
                f"Validation error was:\n{str(e)}"
            )
            raise DBIntegrityError(msg) from e


class ThingNode(BaseModel):
    id: UUID = Field(
        default_factory=uuid.uuid4,
        description="The primary key for the ThingNode table",
    )
    external_id: str = Field(..., description="Externally provided unique identifier")
    stakeholder_key: str = Field(..., description="Stakeholder key for the Thing Node")
    name: str = Field(..., description="Unique name of the Thing Node")
    description: str = Field("", description="Description of the Thing Node")
    parent_node_id: UUID | None = Field(
        None, description="Parent node UUID if this is a child node"
    )
    parent_external_node_id: str | None = Field(
        None, description="Externally provided unique identifier for the parent node"
    )
    # This ID is filled with a dummy-value to enable object creation
    # from a json-file for CompleteStructure
    # It is necessary because at the time of json-creation the real UUID
    # corresponding to the element types external ID is unknown
    element_type_id: UUID = Field(
        default_factory=uuid.uuid4, description="Foreign key to the ElementType table"
    )
    element_type_external_id: str = Field(
        ..., description="Externally provided unique identifier for the element type"
    )
    meta_data: dict[str, Any] | None = Field(
        None, description="Optional metadata for the Thing Node"
    )

    class Config:
        orm_mode = True

    def to_orm_model(self) -> ThingNodeOrm:
        return ThingNodeOrm(
            id=self.id,
            external_id=self.external_id,
            stakeholder_key=self.stakeholder_key,
            name=self.name,
            description=self.description,
            parent_node_id=self.parent_node_id,
            parent_external_node_id=self.parent_external_node_id,
            element_type_id=self.element_type_id,
            element_type_external_id=self.element_type_external_id,
            meta_data=self.meta_data,
        )

    @classmethod
    def from_orm_model(cls, orm_model: ThingNodeOrm) -> "ThingNode":
        try:
            return ThingNode(
                id=orm_model.id,
                external_id=orm_model.external_id,
                stakeholder_key=orm_model.stakeholder_key,
                name=orm_model.name,
                description=orm_model.description,
                parent_node_id=orm_model.parent_node_id,
                parent_external_node_id=orm_model.parent_external_node_id,
                element_type_id=orm_model.element_type_id,
                element_type_external_id=orm_model.element_type_external_id,
                meta_data=orm_model.meta_data,
            )
        except ValidationError as e:
            msg = (
                f"Could not validate db entry for id {orm_model.id}. "
                f"Validation error was:\n{str(e)}"
            )
            raise DBIntegrityError(msg) from e


class FilterType(str, Enum):
    free_text = "free_text"


class Filter(BaseModel):
    name: str = Field(..., description="Name of the filter")
    type: FilterType = Field(..., description="Type of the filter")  # noqa: A003
    required: bool = Field(..., description="Indicates if the filter is required")


class Source(BaseModel):
    id: UUID = Field(default_factory=uuid.uuid4, description="Unique identifier for the source")  # noqa: A003
    external_id: str = Field(..., description="Externally provided unique identifier")
    stakeholder_key: str = Field(..., description="Stakeholder key for the Source")
    name: str = Field(..., description="Name of the source")
    type: ExternalType = Field(..., description="Type of the source")  # noqa: A003
    visible: bool = Field(True, description="Visibility of the source")
    display_path: str = Field(
        "", description="Displays all parent nodes in sequence in the designer frontend"
    )
    preset_filters: dict[str, Any] = Field(
        default_factory=dict, description="Preset filters for the source"
    )
    passthrough_filters: list[Filter] | None = Field(
        None, description="Passthrough filters for the source"
    )
    adapter_key: str = Field(..., description="Adapter key or identifier")
    source_id: str = Field(..., description="Referenced HD Source identifier")
    ref_key: str | None = Field(
        None,
        description="Key of the referenced metadatum, only used for sources of type metadata(any)",
    )
    ref_id: str = Field(
        "",
        description="ID of the thingnode in the mapped adapter hierarchy,"
        " which the mapped source references if source has type metadata(any)",
    )
    meta_data: dict[str, Any] | None = Field(None, description="Optional metadata for the Source")
    thing_node_external_ids: list[str] | None = Field(
        None,
        description="List of externally provided unique identifiers for the thing nodes",
    )

    class Config:
        orm_mode = True

    def to_orm_model(self) -> SourceOrm:
        return SourceOrm(
            id=self.id,
            external_id=self.external_id,
            stakeholder_key=self.stakeholder_key,
            name=self.name,
            type=self.type,
            visible=self.visible,
            display_path=self.display_path,
            preset_filters=self.preset_filters,
            passthrough_filters=[f.dict() for f in self.passthrough_filters]
            if self.passthrough_filters
            else None,
            adapter_key=self.adapter_key,
            source_id=self.source_id,
            ref_key=self.ref_key,
            ref_id=self.ref_id,
            meta_data=self.meta_data,
            thing_node_external_ids=self.thing_node_external_ids
            if self.thing_node_external_ids is not None
            else [],
        )

    @classmethod
    def from_orm_model(cls, orm_model: SourceOrm) -> "Source":
        return Source(
            id=orm_model.id,
            external_id=orm_model.external_id,
            stakeholder_key=orm_model.stakeholder_key,
            name=orm_model.name,
            type=orm_model.type,
            visible=orm_model.visible,
            display_path=orm_model.display_path,
            preset_filters=orm_model.preset_filters,
            passthrough_filters=orm_model.passthrough_filters,
            adapter_key=orm_model.adapter_key,
            source_id=orm_model.source_id,
            ref_key=orm_model.ref_key,
            ref_id=orm_model.ref_id,
            meta_data=orm_model.meta_data,
            thing_node_external_ids=orm_model.thing_node_external_ids,
        )

    @validator("preset_filters", "passthrough_filters", pre=True, each_item=True)
    def validate_filters(cls, v: Any) -> Any:
        if not v:
            return {}
        return v


class Sink(BaseModel):
    id: UUID = Field(default_factory=uuid.uuid4, description="Unique identifier for the sink")  # noqa: A003
    external_id: str = Field(..., description="Externally provided unique identifier")
    stakeholder_key: str = Field(..., description="Stakeholder key for the Sink")
    name: str = Field(..., description="Name of the sink")
    type: ExternalType = Field(..., description="Type of the sink")  # noqa: A003
    visible: bool = Field(True, description="Visibility of the sink")
    display_path: str = Field(
        "", description="Displays all parent nodes in sequence in the designer frontend"
    )
    preset_filters: dict[str, Any] = Field(
        default_factory=dict, description="Preset filters for the sink"
    )
    passthrough_filters: list[Filter] | None = Field(
        None, description="Passthrough filters for the sink"
    )
    adapter_key: str = Field(..., description="Adapter key or identifier")
    sink_id: str = Field(..., description="Referenced HD Sink identifier")
    ref_key: str | None = Field(
        None,
        description="Key of the referenced metadatum, only used for sinks of type metadata(any)",
    )
    ref_id: str = Field(
        "",
        description="ID of the thingnode in the mapped adapter hierarchy,"
        " which the mapped source references if sink has type metadata(any)",
    )
    meta_data: dict[str, Any] | None = Field(None, description="Optional metadata for the Sink")
    thing_node_external_ids: list[str] | None = Field(
        None,
        description="List of externally provided unique identifiers for the thing nodes",
    )

    class Config:
        orm_mode = True

    def to_orm_model(self) -> SinkOrm:
        return SinkOrm(
            id=self.id,
            external_id=self.external_id,
            stakeholder_key=self.stakeholder_key,
            name=self.name,
            type=self.type,
            visible=self.visible,
            display_path=self.display_path,
            preset_filters=self.preset_filters,
            passthrough_filters=[f.dict() for f in self.passthrough_filters]
            if self.passthrough_filters
            else None,
            adapter_key=self.adapter_key,
            sink_id=self.sink_id,
            ref_key=self.ref_key,
            ref_id=self.ref_id,
            meta_data=self.meta_data,
            thing_node_external_ids=self.thing_node_external_ids
            if self.thing_node_external_ids is not None
            else [],
        )

    @classmethod
    def from_orm_model(cls, orm_model: SinkOrm) -> "Sink":
        return Sink(
            id=orm_model.id,
            external_id=orm_model.external_id,
            stakeholder_key=orm_model.stakeholder_key,
            name=orm_model.name,
            type=orm_model.type,
            visible=orm_model.visible,
            display_path=orm_model.display_path,
            preset_filters=orm_model.preset_filters,
            passthrough_filters=orm_model.passthrough_filters,
            adapter_key=orm_model.adapter_key,
            sink_id=orm_model.sink_id,
            ref_key=orm_model.ref_key,
            ref_id=orm_model.ref_id,
            meta_data=orm_model.meta_data,
            thing_node_external_ids=orm_model.thing_node_external_ids,
        )

    @validator("preset_filters", "passthrough_filters", pre=True, each_item=True)
    def validate_filters(cls, v: Any) -> Any:
        if not v:
            return {}
        return v


class CompleteStructure(BaseModel):
    element_types: list[ElementType] = Field(..., description="All element types of the structure")
    thing_nodes: list[ThingNode] = Field(
        default_factory=list, description="All thingnodes of the structure"
    )
    sources: list[Source] = Field(default_factory=list, description="All sources of the structure")
    sinks: list[Sink] = Field(default_factory=list, description="All sinks of the structure")

    # Root validator to check if each parent_external_node_id exists in at least one other node
    @root_validator(pre=True)
    def validate_root_nodes(cls, values: dict[str, Any]) -> dict[str, Any]:
        nodes = values.get("thing_nodes", [])
        # Create a set of all external_ids in the thing_nodes list
        external_ids = {node["external_id"] for node in nodes}

        for node in nodes:
            parent_ext_id = node.get("parent_external_node_id")
            if parent_ext_id is not None and parent_ext_id not in external_ids:
                # Raise an error if the parent_external_node_id does not exist in the other nodes
                raise ValueError(
                    f"Root node '{node.get('name')}' has an invalid "
                    f"parent_external_node_id '{parent_ext_id}' that does "
                    "not reference any existing ThingNode."
                )
        return values

    @root_validator(pre=True)
    def check_stakeholder_key_consistency(cls, values: dict[str, Any]) -> dict[str, Any]:
        stakeholder_keys = set()

        for node in values.get("thing_nodes", []):
            stakeholder_keys.add(node["stakeholder_key"])

        for element_type in values.get("element_types", []):
            stakeholder_keys.add(element_type["stakeholder_key"])

        if len(stakeholder_keys) > 1:
            sorted_keys = sorted(stakeholder_keys)
            raise ValueError(
                f"Inconsistent stakeholder keys found: {set(sorted_keys)}. "
                "All stakeholder keys must be consistent across element_types and thing_nodes."
            )

        return values

    @root_validator(pre=True)
    def check_for_circular_reference(cls, values: dict[str, Any]) -> dict[str, Any]:
        nodes_by_external_id = {node["external_id"]: node for node in values.get("thing_nodes", [])}
        visited = set()

        def visit(node: dict[str, Any]) -> None:
            if node["external_id"] in visited:
                raise ValueError(f"Circular reference detected in node {node['external_id']}")
            visited.add(node["external_id"])
            parent_external_id = node.get("parent_external_node_id")
            if parent_external_id and parent_external_id in nodes_by_external_id:
                visit(nodes_by_external_id[parent_external_id])
            visited.remove(node["external_id"])  # Remove node from visited after visiting

        for node in values.get("thing_nodes", []):
            if node["external_id"] not in visited:
                visit(node)
        return values

    @root_validator(pre=True)
    def check_unique_external_ids(cls, values: dict[str, Any]) -> dict[str, Any]:
        unique_check = {
            "element_types": set(),
            "thing_nodes": set(),
            "sources": set(),
            "sinks": set(),
        }
        for category in unique_check.keys():
            for item in values.get(category, []):
                if item["external_id"] in unique_check[category]:
                    raise ValueError(
                        f"Duplicate external_id '{item['external_id']}' found in {category}."
                    )
                unique_check[category].add(item["external_id"])
        return values

    @root_validator(pre=True)
    def validate_source_sink_references(cls, values: dict[str, Any]) -> dict[str, Any]:
        thing_node_ids = {node["external_id"] for node in values.get("thing_nodes", [])}
        for source in values.get("sources", []):
            for tn_id in source.get("thing_node_external_ids", []):
                if tn_id not in thing_node_ids:
                    raise ValueError(
                        f"Source '{source['external_id']}' references "
                        f"non-existing ThingNode '{tn_id}'."
                    )
        for sink in values.get("sinks", []):
            for tn_id in sink.get("thing_node_external_ids", []):
                if tn_id not in thing_node_ids:
                    raise ValueError(
                        f"Sink '{sink['external_id']}' references "
                        f"non-existing ThingNode '{tn_id}'."
                    )
        return values

    @validator("sources", "sinks", pre=True, each_item=True)
    def validate_passthrough_filters(cls, v: Any) -> Any:
        for filter in v.get("passthrough_filters", []):
            if "name" not in filter or not isinstance(filter["name"], str):
                raise ValueError("Each passthrough filter must have a 'name' of type str.")
            if "type" not in filter or filter["type"] not in ["free_text", "number", "date"]:
                raise ValueError("Each passthrough filter must have a valid 'type'.")
            if "required" not in filter or not isinstance(filter["required"], bool):
                raise ValueError("Each passthrough filter must have a 'required' boolean field.")
        return v
