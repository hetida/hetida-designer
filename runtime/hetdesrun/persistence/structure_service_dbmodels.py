from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, declarative_base, relationship, validates
from sqlalchemy.types import JSON
from sqlalchemy_utils import UUIDType

Base = declarative_base()


class ElementTypeOrm(Base):
    __tablename__ = "element_type"
    id: UUIDType = Column(
        "id",
        UUIDType(binary=False),
        primary_key=True,
        nullable=False,
        default=uuid4,
    )
    name = Column(String(255), index=True, nullable=False, unique=True)
    icon = Column(String(255), nullable=True)
    description = Column(String(1024), nullable=True)
    property_sets: list["PropertySetOrm"] = relationship(
        "PropertySetOrm",
        secondary="element_type_to_property_set",
        back_populates="element_types",
        uselist=True,
    )
    thing_nodes: list["ThingNodeOrm"] = relationship(
        "ThingNodeOrm", back_populates="element_type"
    )

    __table_args__ = (UniqueConstraint("name", name="_element_type_name_uc"),)


class PropertyMetadataOrm(Base):
    __tablename__ = "property_metadata"
    id: UUIDType = Column(
        "id",
        UUIDType(binary=False),
        primary_key=True,
        nullable=False,
        default=uuid4,
    )
    property_set_id: UUIDType = Column(
        UUIDType(binary=False),
        ForeignKey("property_set.id"),
        nullable=False,
    )
    column_name = Column(String(255), nullable=False)
    column_label = Column(String(255), nullable=False)
    column_type = Column(Enum("STRING", "INT", "FLOAT", "BOOLEAN"))
    field_length = Column(Integer, nullable=True)
    nullable = Column(Boolean, default=True, nullable=False)
    order_no = Column(Integer, nullable=False)
    property_set: Optional["PropertySetOrm"] = relationship(
        "PropertySetOrm",
        back_populates="properties_metadata",
        uselist=False,
        cascade="all",
    )
    __table_args__ = (
        CheckConstraint("field_length > 0", name="_field_length_positive_ck"),
        UniqueConstraint("property_set_id", name="_property_metadata_psid_uc"),
    )


class PropertySetOrm(Base):
    __tablename__ = "property_set"
    id: UUIDType = Column(
        "id",
        UUIDType(binary=False),
        primary_key=True,
        nullable=False,
        default=uuid4,
    )
    name = Column(String(255), index=True, nullable=False)
    description = Column(String(1024), nullable=True)
    reference_table_name = Column(String(100), unique=True, nullable=False)
    property_set_type = Column(String(50), nullable=False)
    element_types: list[ElementTypeOrm] = relationship(
        "ElementTypeOrm",
        secondary="element_type_to_property_set",
        back_populates="property_sets",
        uselist=True,
    )
    properties_metadata: list[PropertyMetadataOrm] = relationship(
        "PropertyMetadataOrm",
        back_populates="property_set",
        cascade="all, delete-orphan",
    )

    __table_args__ = (UniqueConstraint("name", name="_property_set_name_uc"),)

    @validates("property_set_type")
    def validate_property_set_type(self, key: str, value: str) -> str:  # noqa: ARG002
        valid_types = ["INTERNAL", "EXTERNAL"]
        if value not in valid_types:
            raise ValueError(f"Invalid value for {key}: {value}")
        return value


class ThingNodeOrm(Base):
    __tablename__ = "thing_node"

    id: UUIDType = Column("id", UUIDType(binary=False), primary_key=True, default=uuid4)
    name = Column(String(255), index=True, nullable=False, unique=True)
    description = Column(String(1024), nullable=True)
    parent_node_id: UUIDType = Column(
        UUIDType(binary=False), ForeignKey("thing_node.id"), nullable=True
    )
    element_type_id: UUIDType = Column(
        UUIDType(binary=False),
        ForeignKey("element_type.id"),
        nullable=False,
    )
    entity_uuid = Column(String(36), nullable=False)
    meta_data = Column(JSON, nullable=True)
    element_type: Mapped["ElementTypeOrm"] = relationship(
        "ElementTypeOrm", back_populates="thing_nodes", uselist=False
    )
    sources = relationship(
        "SourceOrm", back_populates="thing_node", cascade="all, delete-orphan"
    )
    sinks = relationship(
        "SinkOrm", back_populates="thing_node", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("name", name="_thing_node_name_uc"),)


class SourceOrm(Base):
    __tablename__ = "source"

    id = Column(UUIDType(binary=False), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False, unique=True)
    type = Column(String(255), nullable=False)
    visible = Column(Boolean, default=True)
    adapter_key = Column(String(255), nullable=False)
    source_id = Column(UUIDType(binary=False), nullable=False)
    thing_node_id = Column(UUIDType(binary=False), ForeignKey("thing_node.id"))
    thing_node = relationship("ThingNodeOrm", back_populates="sources")
    preset_filters = Column(JSON, nullable=True)
    passthrough_filters = Column(JSON, nullable=True)


class SinkOrm(Base):
    __tablename__ = "sink"

    id = Column(UUIDType(binary=False), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False, unique=True)
    type = Column(String(255), nullable=False)
    visible = Column(Boolean, default=True)
    adapter_key = Column(String(255), nullable=False)
    sink_id = Column(UUIDType(binary=False), nullable=False)
    thing_node_id = Column(UUIDType(binary=False), ForeignKey("thing_node.id"))
    thing_node = relationship("ThingNodeOrm", back_populates="sinks")
    preset_filters = Column(JSON, nullable=True)
    passthrough_filters = Column(JSON, nullable=True)


class ElementTypeToPropertySetOrm(Base):
    __tablename__ = "element_type_to_property_set"
    element_type_id: UUIDType = Column(
        UUIDType(binary=False),
        ForeignKey("element_type.id", ondelete="CASCADE"),
        primary_key=True,
    )
    property_set_id: UUIDType = Column(
        UUIDType(binary=False),
        ForeignKey("property_set.id", ondelete="CASCADE"),
        primary_key=True,
    )
    order_no = Column(Integer, nullable=False)
