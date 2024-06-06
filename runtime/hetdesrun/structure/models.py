from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field, ValidationError, validator

from hetdesrun.persistence.dbmodels import (
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
    id: int | None = Field(None, description="The primary key for the ThingNode table")
    name: str = Field(..., description="Unique name of the Thing Node")
    description: str | None = Field(None, description="Description of the Thing Node")
    parent_node_id: int | None = Field(
        None, description="Parent node ID if this is a child node"
    )
    element_type_id: int = Field(
        ..., description="Foreign key to the ElementType table"
    )
    entity_uuid: str = Field(..., description="UUID identifier for the entity")
    children: list["ThingNode"] = Field(
        default_factory=list, description="List of child ThingNodes"
    )
    source: Optional["Source"] = Field(
        None, description="Source associated with the ThingNode"
    )
    sink: Optional["Sink"] = Field(
        None, description="Sink associated with the ThingNode"
    )

    class Config:
        orm_mode = True

    def to_orm_model(self) -> ThingNodeOrm:
        return ThingNodeOrm(
            id=self.id,
            name=self.name,
            description=self.description,
            parent_node_id=self.parent_node_id,
            element_type_id=self.element_type_id,
            entity_uuid=self.entity_uuid,
            children=[child.to_orm_model() for child in self.children],
            source=self.source.to_orm_model() if self.source else None,
            sink=self.sink.to_orm_model() if self.sink else None,
        )

    @classmethod
    def from_orm_model(cls, orm_model: ThingNodeOrm) -> "ThingNode":
        try:
            return ThingNode(
                id=orm_model.id,
                name=orm_model.name,
                description=orm_model.description,
                parent_node_id=orm_model.parent_node_id,
                element_type_id=orm_model.element_type_id,
                entity_uuid=orm_model.entity_uuid,
                children=[cls.from_orm_model(child) for child in orm_model.children],
                source=Source.from_orm_model(orm_model.source)
                if orm_model.source
                else None,
                sink=Sink.from_orm_model(orm_model.sink) if orm_model.sink else None,
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
    name: str
    type: FilterType  # noqa: A003
    required: bool


class Source(BaseModel):
    id: int  # noqa: A003
    thingNodeId: int | None
    name: str
    type: ExternalType  # noqa: A003
    visible: bool | None = True
    path: str
    metadataKey: str | None = None
    filters: dict[str, Filter] | None = {}

    class Config:
        orm_model = True

    def to_orm_model(self) -> SourceOrm:
        return SourceOrm(
            id=self.id,
            thing_node_id=self.thingNodeId,
            name=self.name,
            type=self.type,
            visible=self.visible,
            path=self.path,
            metadata_key=self.metadataKey,
            filters=self.filters,
        )

    @classmethod
    def from_orm_model(cls, orm_model: SourceOrm) -> "Source":
        return Source(
            id=orm_model.id,
            thingNodeId=orm_model.thing_node_id,
            name=orm_model.name,
            type=orm_model.type,
            visible=orm_model.visible,
            path=orm_model.path,
            metadataKey=orm_model.metadata_key,
            filters=orm_model.filters,
        )


class Sink(BaseModel):
    id: int  # noqa: A003
    thingNodeId: int | None
    name: str
    type: ExternalType  # noqa: A003
    visible: bool | None = True
    path: str
    metadataKey: str | None = None
    filters: dict[str, Filter] | None = {}

    class Config:
        orm_model = True

    def to_orm_model(self) -> SinkOrm:
        return SinkOrm(
            id=self.id,
            thing_node_id=self.thingNodeId,
            name=self.name,
            type=self.type,
            visible=self.visible,
            path=self.path,
            metadata_key=self.metadataKey,
            filters=self.filters,
        )

    @classmethod
    def from_orm_model(cls, orm_model: SinkOrm) -> "Sink":
        return Sink(
            id=orm_model.id,
            thingNodeId=orm_model.thing_node_id,
            name=orm_model.name,
            type=orm_model.type,
            visible=orm_model.visible,
            path=orm_model.path,
            metadataKey=orm_model.metadata_key,
            filters=orm_model.filters,
        )


class PropertySet(BaseModel):
    id: int | None = Field(None, description="The primary key for the PropertySet")
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
    id: int | None = Field(
        None, description="The primary key for the ElementType table"
    )
    name: str = Field(..., description="Unique name of the ElementType")
    icon: str | None = Field(None, description="Icon representing the ElementType")
    description: str | None = Field(None, description="Description of the ElementType")
    property_sets: list[PropertySet] = Field(
        default_factory=list, description="List of associated PropertySets"
    )
    thing_nodes: list[ThingNode] = Field(
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
    id: int | None = Field(
        None, description="The primary key ID of the property metadata."
    )
    property_set_id: int | None = Field(
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
    element_type_id: int = Field(
        ..., description="The foreign key ID linking to the ElementType."
    )
    property_set_id: int = Field(
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
