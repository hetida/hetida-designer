from enum import Enum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, ValidationError, validator

from hetdesrun.persistence.structure_service_dbmodels import (
    ElementTypeOrm,
    ElementTypeToPropertySetOrm,
    PropertyMetadataOrm,
    PropertySetOrm,
    SinkOrm,
    SourceOrm,
    ThingNodeOrm,
)
from hetdesrun.structure.db.exceptions import DBIntegrityError
from hetdesrun.structure.db.external_types import ExternalType


class ThingNode(BaseModel):
    id: UUID = Field(..., description="The primary key for the ThingNode table")
    external_id: str = Field(..., description="Externally provided unique identifier")
    name: str = Field(..., description="Unique name of the Thing Node")
    description: str = Field("", description="Description of the Thing Node")
    parent_node_id: UUID | None = Field(
        None, description="Parent node UUID if this is a child node"
    )
    element_type_id: UUID = Field(
        ..., description="Foreign key to the ElementType table"
    )
    meta_data: dict[str, Any] | None = Field(
        None, description="Optional metadata for the Thing Node"
    )
    sources: list[UUID] = Field(default_factory=list, description="List of source IDs")
    sinks: list[UUID] = Field(default_factory=list, description="List of sink IDs")

    class Config:
        orm_mode = True

    def to_orm_model(self) -> ThingNodeOrm:
        return ThingNodeOrm(
            id=self.id,
            external_id=self.external_id,
            name=self.name,
            description=self.description,
            parent_node_id=self.parent_node_id,
            element_type_id=self.element_type_id,
            meta_data=self.meta_data,
        )

    @classmethod
    def from_orm_model(cls, orm_model: ThingNodeOrm) -> "ThingNode":
        try:
            return ThingNode(
                id=orm_model.id,
                external_id=orm_model.external_id,
                name=orm_model.name,
                description=orm_model.description,
                parent_node_id=orm_model.parent_node_id,
                element_type_id=orm_model.element_type_id,
                meta_data=orm_model.meta_data,
                sources=[source.id for source in orm_model.sources],
                sinks=[sink.id for sink in orm_model.sinks],
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
    id: UUID = Field(..., description="Unique identifier for the source")  # noqa: A003
    name: str = Field(..., description="Name of the source")
    type: ExternalType = Field(..., description="Type of the source")  # noqa: A003
    visible: bool = Field(True, description="Visibility of the source")
    preset_filters: dict[str, Any] | None = Field(
        None, description="Preset filters for the source"
    )
    passthrough_filters: list[str] | None = Field(
        None, description="Passthrough filters for the source"
    )
    adapter_key: str | int = Field(..., description="Adapter key or identifier")
    source_id: UUID = Field(..., description="Referenced HD Source identifier")
    meta_data: dict[str, Any] | None = Field(
        None, description="Optional metadata for the Thing Node"
    )

    class Config:
        orm_mode = True

    def to_orm_model(self) -> SourceOrm:
        return SourceOrm(
            id=self.id,
            name=self.name,
            type=self.type,
            visible=self.visible,
            preset_filters=self.preset_filters,
            passthrough_filters=self.passthrough_filters,
            adapter_key=self.adapter_key,
            source_id=self.source_id,
            meta_data=self.meta_data,
        )

    @classmethod
    def from_orm_model(cls, orm_model: SourceOrm) -> "Source":
        return Source(
            id=orm_model.id,
            name=orm_model.name,
            type=orm_model.type,
            visible=orm_model.visible,
            preset_filters=orm_model.preset_filters,
            passthrough_filters=orm_model.passthrough_filters,
            adapter_key=orm_model.adapter_key,
            source_id=orm_model.source_id,
            meta_data=orm_model.meta_data,
        )

    @validator("preset_filters", "passthrough_filters", pre=True, each_item=True)
    def validate_filters(cls, v):
        if not v:
            return {}
        return v


class Sink(BaseModel):
    id: UUID = Field(..., description="Unique identifier for the sink")  # noqa: A003
    name: str = Field(..., description="Name of the sink")
    type: ExternalType = Field(..., description="Type of the sink")  # noqa: A003
    visible: bool = Field(True, description="Visibility of the sink")
    preset_filters: dict[str, Any] | None = Field(
        None, description="Preset filters for the sink"
    )
    passthrough_filters: list[str] | None = Field(
        None, description="Passthrough filters for the sink"
    )
    adapter_key: str | int = Field(..., description="Adapter key or identifier")
    sink_id: UUID = Field(..., description="Referenced HD Sink identifier")
    meta_data: dict[str, Any] | None = Field(
        None, description="Optional metadata for the Thing Node"
    )

    class Config:
        orm_mode = True

    def to_orm_model(self) -> SinkOrm:
        return SinkOrm(
            id=self.id,
            name=self.name,
            type=self.type,
            visible=self.visible,
            preset_filters=self.preset_filters,
            passthrough_filters=self.passthrough_filters,
            adapter_key=self.adapter_key,
            sink_id=self.sink_id,
            meta_data=self.meta_data,
        )

    @classmethod
    def from_orm_model(cls, orm_model: SinkOrm) -> "Sink":
        return Sink(
            id=orm_model.id,
            name=orm_model.name,
            type=orm_model.type,
            visible=orm_model.visible,
            preset_filters=orm_model.preset_filters,
            passthrough_filters=orm_model.passthrough_filters,
            adapter_key=orm_model.adapter_key,
            sink_id=orm_model.sink_id,
            meta_data=orm_model.meta_data,
        )

    @validator("preset_filters", "passthrough_filters", pre=True, each_item=True)
    def validate_filters(cls, v):
        if not v:
            return {}
        return v


class PropertySet(BaseModel):
    id: UUID = Field(..., description="The primary key for the PropertySet")
    name: str = Field(..., description="The name of the PropertySet.")
    description: str | None = Field(
        None, description="A detailed description of the PropertySet."
    )
    reference_table_name: str = Field(
        ..., description="The database table name associated with this PropertySet."
    )
    property_set_type: str = Field(
        ..., description="The type of PropertySet, either 'INTERNAL' or 'EXTERNAL'."
    )

    class Config:
        orm_mode = True

    def to_orm_model(self) -> PropertySetOrm:
        return PropertySetOrm(
            id=self.id,
            name=self.name,
            description=self.description,
            reference_table_name=self.reference_table_name,
            property_set_type=self.property_set_type,
        )

    @classmethod
    def from_orm_model(cls, orm_model: PropertySetOrm) -> "PropertySet":
        try:
            return PropertySet(
                id=orm_model.id,
                name=orm_model.name,
                description=orm_model.description,
                reference_table_name=orm_model.reference_table_name,
                property_set_type=orm_model.property_set_type,
            )
        except ValidationError as e:
            msg = (
                f"Could not validate db entry for id {orm_model.id}. "
                f"Validation error was:\n{str(e)}"
            )
            raise DBIntegrityError(msg) from e

    @validator("property_set_type")
    def check_type(cls, v: str) -> str:
        valid_types = ["INTERNAL", "EXTERNAL"]
        if v not in valid_types:
            raise ValueError(
                "property_set_type must be either 'INTERNAL' or 'EXTERNAL'"
            )
        return v


class ElementType(BaseModel):
    id: UUID = Field(..., description="The primary key for the ElementType table")
    name: str = Field(..., description="Unique name of the ElementType")
    icon: str | None = Field(None, description="Icon representing the ElementType")
    description: str | None = Field(None, description="Description of the ElementType")
    property_sets: list[PropertySet] = Field(
        default_factory=list, description="List of associated PropertySets"
    )
    thing_nodes: list["ThingNode"] = Field(
        default_factory=list, description="List of associated ThingNodes"
    )

    class Config:
        orm_mode = True

    def to_orm_model(self) -> ElementTypeOrm:
        return ElementTypeOrm(
            id=self.id,
            name=self.name,
            icon=self.icon,
            description=self.description,
            property_sets=[ps.to_orm_model() for ps in self.property_sets],
            thing_nodes=[tn.to_orm_model() for tn in self.thing_nodes],
        )

    @classmethod
    def from_orm_model(cls, orm_model: ElementTypeOrm) -> "ElementType":
        try:
            return cls(
                id=orm_model.id,
                name=orm_model.name,
                icon=orm_model.icon,
                description=orm_model.description,
            )
        except ValidationError as e:
            msg = (
                f"Could not validate db entry for id {orm_model.id}. "
                f"Validation error was:\n{str(e)}"
            )
            raise DBIntegrityError(msg) from e


class PropertyMetadata(BaseModel):
    id: UUID = Field(..., description="The primary key ID of the property metadata.")
    property_set_id: UUID | None = Field(
        None, description="The foreign key ID linking to the Property Set."
    )
    column_name: str = Field(
        ..., description="The name of the column in the property set."
    )
    column_label: str = Field(
        ..., description="The label of the column for display purposes."
    )
    column_type: Literal["STRING", "INT", "FLOAT", "BOOLEAN"] = Field(
        ..., description="The data type of the column (STRING, INT, FLOAT, BOOLEAN)."
    )
    field_length: int | None = Field(
        None, description="The length of the field, applicable for STRING type columns."
    )
    nullable: bool = Field(
        ..., description="Indicates if the column can accept NULL values."
    )
    order_no: int = Field(
        ..., description="The ordering number of the column within the property set."
    )

    @validator("field_length")
    def field_length_must_be_positive(cls, v: int | None) -> int | None:
        if v is not None and v <= 0:
            raise ValueError("field_length must be positive if specified")
        return v

    class Config:
        orm_mode = True

    def to_orm_model(self) -> PropertyMetadataOrm:
        return PropertyMetadataOrm(
            id=self.id,
            property_set_id=self.property_set_id,
            column_name=self.column_name,
            column_label=self.column_label,
            column_type=self.column_type,
            field_length=self.field_length,
            nullable=self.nullable,
            order_no=self.order_no,
        )

    @classmethod
    def from_orm_model(cls, orm_model: PropertyMetadataOrm) -> "PropertyMetadata":
        try:
            return cls(
                id=orm_model.id,
                property_set_id=orm_model.property_set_id,
                column_name=orm_model.column_name,
                column_label=orm_model.column_label,
                column_type=orm_model.column_type,
                field_length=orm_model.field_length,
                nullable=orm_model.nullable,
                order_no=orm_model.order_no,
            )
        except ValidationError as e:
            msg = (
                f"Could not validate db entry for id {orm_model.id}. "
                f"Validation error was:\n{str(e)}"
            )
            raise DBIntegrityError(msg) from e


class ElementTypeToPropertySet(BaseModel):
    element_type_id: UUID = Field(
        ..., description="The foreign key ID linking to the ElementType."
    )
    property_set_id: UUID = Field(
        ..., description="The foreign key ID linking to the PropertySet."
    )
    order_no: int = Field(
        ...,
        description="The order number for the property set in relation to the element type",
    )

    class Config:
        orm_mode = True

    def to_orm_model(self) -> ElementTypeToPropertySetOrm:
        return ElementTypeToPropertySetOrm(
            element_type_id=self.element_type_id,
            property_set_id=self.property_set_id,
            order_no=self.order_no,
        )

    @classmethod
    def from_orm_model(
        cls, orm_model: ElementTypeToPropertySetOrm
    ) -> "ElementTypeToPropertySet":
        return cls(
            element_type_id=orm_model.element_type_id,
            property_set_id=orm_model.property_set_id,
            order_no=orm_model.order_no,
        )


class CompleteStructure(BaseModel):
    thing_nodes: list[ThingNode] = Field(
        ..., description="All thingnodes of the structure"
    )
    sources: list[Source] = Field(..., description="All sources of the structure")
    sinks: list[Sink] = Field(..., description="All sinks of the structure")
    element_types: list[ElementType] = Field(
        ..., description="All element types of the structure"
    )
