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
from sqlalchemy_utils import UUIDType

Base = declarative_base()


class ElementTypeOrm(Base):
    __tablename__ = "element_type"
    id: UUIDType = Column(
        "element_type_id",
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
        "property_metadata_id",
        UUIDType(binary=False),
        primary_key=True,
        nullable=False,
        default=uuid4,
    )
    property_set_id: UUIDType = Column(
        UUIDType(binary=False),
        ForeignKey("property_set.property_set_id"),
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
        "property_set_id",
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

    id: UUIDType = Column(
        "thing_node_id", UUIDType(binary=False), primary_key=True, default=uuid4
    )
    external_id = Column(String(36), nullable=False, unique=True, index=True)
    name = Column(String(255), index=True, nullable=False, unique=True)
    description = Column(String(1024), nullable=True)
    parent_node_id: UUIDType = Column(
        UUIDType(binary=False), ForeignKey("thing_node.thing_node_id"), nullable=True
    )
    element_type_id: UUIDType = Column(
        UUIDType(binary=False),
        ForeignKey("element_type.element_type_id"),
        nullable=False,
    )
    meta_data = Column(JSON, nullable=True)
    element_type: Mapped["ElementTypeOrm"] = relationship(
        "ElementTypeOrm", back_populates="thing_nodes", uselist=False
    )
    sources: list["SourceOrm"] = relationship(
        "SourceOrm",
        secondary="thingnode_source_association",
        back_populates="thing_nodes",
    )
    sinks: list["SinkOrm"] = relationship(
        "SinkOrm", secondary="thingnode_sink_association", back_populates="thing_nodes"
    )

    __table_args__ = (UniqueConstraint("name", name="_thing_node_name_uc"),)

    def __repr__(self) -> str:
        return (
            f"<ThingNodeOrm(id={self.id}, parent_node_id={self.parent_node_id}, "
            f"sources={[source.id for source in self.sources]}, "
            f"sinks={[sink.id for sink in self.sinks]})>"
        )


class SourceOrm(Base):
    __tablename__ = "source"

    id: UUIDType = Column(UUIDType(binary=False), primary_key=True, default=uuid4)
    name: str = Column(String(255), nullable=False, unique=True)
    type: str = Column(String(255), nullable=False)
    visible: bool = Column(Boolean, default=True)
    adapter_key: str = Column(String(255), nullable=False)
    source_id: UUIDType = Column(UUIDType(binary=False), nullable=False)
    meta_data: dict | None = Column(JSON, nullable=True)
    thing_node_id: UUIDType | None = Column(
        UUIDType(binary=False), ForeignKey("thing_node.thing_node_id")
    )
    thing_node: Optional["ThingNodeOrm"] = relationship(
        "ThingNodeOrm", back_populates="sources"
    )
    preset_filters: dict | None = Column(JSON, nullable=True)
    passthrough_filters: list[str] | None = Column(JSON, nullable=True)
    thing_nodes: list["ThingNodeOrm"] = relationship(
        "ThingNodeOrm",
        secondary="thingnode_source_association",
        back_populates="sources",
    )


class SinkOrm(Base):
    __tablename__ = "sink"

    id: UUIDType = Column(UUIDType(binary=False), primary_key=True, default=uuid4)
    name: str = Column(String(255), nullable=False, unique=True)
    type: str = Column(String(255), nullable=False)
    visible: bool = Column(Boolean, default=True)
    adapter_key: str = Column(String(255), nullable=False)
    sink_id: UUIDType = Column(UUIDType(binary=False), nullable=False)
    meta_data: dict | None = Column(JSON, nullable=True)
    thing_node_id: UUIDType | None = Column(
        UUIDType(binary=False), ForeignKey("thing_node.thing_node_id")
    )
    thing_node: Optional["ThingNodeOrm"] = relationship(
        "ThingNodeOrm", back_populates="sinks"
    )
    preset_filters: dict | None = Column(JSON, nullable=True)
    passthrough_filters: list[str] | None = Column(JSON, nullable=True)
    thing_nodes: list["ThingNodeOrm"] = relationship(
        "ThingNodeOrm",
        secondary="thingnode_sink_association",
        back_populates="sinks",
    )


class ThingNodeSourceAssociation(Base):
    __tablename__ = "thingnode_source_association"
    thing_node_id: UUIDType = Column(
        UUIDType(binary=False), ForeignKey("thing_node.thing_node_id"), primary_key=True
    )
    source_id: UUIDType = Column(
        UUIDType(binary=False), ForeignKey("source.id"), primary_key=True
    )


class ThingNodeSinkAssociation(Base):
    __tablename__ = "thingnode_sink_association"
    thing_node_id: UUIDType = Column(
        UUIDType(binary=False), ForeignKey("thing_node.thing_node_id"), primary_key=True
    )
    sink_id: UUIDType = Column(
        UUIDType(binary=False), ForeignKey("sink.id"), primary_key=True
    )


class ElementTypeToPropertySetOrm(Base):
    __tablename__ = "element_type_to_property_set"
    element_type_id: UUIDType = Column(
        UUIDType(binary=False),
        ForeignKey("element_type.element_type_id", ondelete="CASCADE"),
        primary_key=True,
    )
    property_set_id: UUIDType = Column(
        UUIDType(binary=False),
        ForeignKey("property_set.property_set_id", ondelete="CASCADE"),
        primary_key=True,
    )
    order_no = Column(Integer, nullable=False)
