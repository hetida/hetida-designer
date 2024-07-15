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
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, declarative_base, relationship, validates
from sqlalchemy_utils import UUIDType

Base = declarative_base()


class ElementTypeOrm(Base):
    __tablename__ = "element_type"
    id: UUIDType = Column(
        UUIDType(binary=False),
        primary_key=True,
        nullable=False,
        default=uuid4,
    )
    external_id = Column(String(255), nullable=False)
    stakeholder_key = Column(String(36), nullable=False)
    name = Column(String(255), index=True, nullable=False, unique=True)
    description = Column(String(1024), nullable=True)
    property_sets: list["PropertySetOrm"] = relationship(
        "PropertySetOrm",
        secondary="element_type_to_property_set",
        back_populates="element_types",
        uselist=True,
    )
    thing_nodes: list["ThingNodeOrm"] = relationship("ThingNodeOrm", back_populates="element_type")

    __table_args__ = (
        UniqueConstraint("name", name="_element_type_name_uc"),
        UniqueConstraint(
            "external_id",
            "stakeholder_key",
            name="_element_type_external_id_stakeholder_key_uc",
        ),
    )


class ThingNodeOrm(Base):
    __tablename__ = "thing_node"
    id: UUIDType = Column(UUIDType(binary=False), primary_key=True, default=uuid4)
    external_id = Column(String(255), nullable=False)
    stakeholder_key = Column(String(36), nullable=False)
    name = Column(String(255), index=True, nullable=False, unique=True)
    description = Column(String(1024), nullable=True)
    parent_node_id: UUIDType = Column(
        UUIDType(binary=False), ForeignKey("thing_node.id"), nullable=True
    )
    parent_external_node_id = Column(String(255), nullable=True)
    element_type_id: UUIDType = Column(
        UUIDType(binary=False),
        ForeignKey("element_type.id"),
        nullable=False,
    )
    element_type_external_id = Column(String(255), nullable=False)
    meta_data = Column(JSON, nullable=True)
    element_type: Mapped["ElementTypeOrm"] = relationship(
        "ElementTypeOrm", back_populates="thing_nodes", uselist=False
    )

    __table_args__ = (
        UniqueConstraint("name", name="_thing_node_name_uc"),
        UniqueConstraint(
            "external_id",
            "stakeholder_key",
            name="_thing_node_external_id_stakeholder_key_uc",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<ThingNodeOrm(id={self.id}, parent_node_id={self.parent_node_id}, "
            f"sources={[source.id for source in self.sources]}, "
            f"sinks={[sink.id for sink in self.sinks]})>"
        )


class SourceOrm(Base):
    __tablename__ = "source"
    id: UUIDType = Column(UUIDType(binary=False), primary_key=True, default=uuid4)
    external_id = Column(String(255), nullable=False)
    stakeholder_key = Column(String(36), nullable=False)
    name: str = Column(String(255), nullable=False, unique=True)
    type: str = Column(String(255), nullable=False)
    visible: bool = Column(Boolean, default=True)
    adapter_key: str = Column(String(255), nullable=False)
    source_id: str = Column(String(255), nullable=False)
    meta_data: dict | None = Column(JSON, nullable=True)
    preset_filters: dict | None = Column(JSON, nullable=True)
    passthrough_filters: list[str] | None = Column(JSON, nullable=True)
    thing_node_external_ids: list[str] = Column(JSON, nullable=True)

    thing_nodes: list["ThingNodeOrm"] = relationship(
        "ThingNodeOrm",
        secondary="thingnode_source_association"
    )

    __table_args__ = (
        UniqueConstraint(
            "external_id",
            "stakeholder_key",
            name="_source_external_id_stakeholder_key_uc",
        ),
    )


class SinkOrm(Base):
    __tablename__ = "sink"

    id: UUIDType = Column(UUIDType(binary=False), primary_key=True, default=uuid4)
    external_id = Column(String(255), nullable=False)
    stakeholder_key = Column(String(36), nullable=False)
    name: str = Column(String(255), nullable=False, unique=True)
    type: str = Column(String(255), nullable=False)
    visible: bool = Column(Boolean, default=True)
    adapter_key: str = Column(String(255), nullable=False)
    sink_id: str = Column(String(255), nullable=False)
    meta_data: dict | None = Column(JSON, nullable=True)
    preset_filters: dict | None = Column(JSON, nullable=True)
    passthrough_filters: list[str] | None = Column(JSON, nullable=True)
    thing_node_external_ids: list[str] = Column(JSON, nullable=True)

    thing_nodes: list["ThingNodeOrm"] = relationship(
        "ThingNodeOrm",
        secondary="thingnode_sink_association"
    )

    __table_args__ = (
        UniqueConstraint(
            "external_id",
            "stakeholder_key",
            name="_sink_external_id_stakeholder_key_uc",
        ),
    )


thingnode_source_association = Table(
    "thingnode_source_association",
    Base.metadata,
    Column("thing_node_id", UUIDType(binary=False), ForeignKey("thing_node.id"), primary_key=True),
    Column("source_id", UUIDType(binary=False), ForeignKey("source.id"), primary_key=True),
)

thingnode_sink_association = Table(
    "thingnode_sink_association",
    Base.metadata,
    Column("thing_node_id", UUIDType(binary=False), ForeignKey("thing_node.id"), primary_key=True),
    Column("sink_id", UUIDType(binary=False), ForeignKey("sink.id"), primary_key=True),
)


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


class PropertyMetadataOrm(Base):
    __tablename__ = "property_metadata"
    id: UUIDType = Column(
        UUIDType(binary=False),
        primary_key=True,
        nullable=False,
        default=uuid4,
    )
    external_id = Column(String(255), nullable=False)
    stakeholder_key = Column(String(36), nullable=False)
    property_set_id: UUIDType = Column(
        UUIDType(binary=False),
        ForeignKey("property_set.id"),
        nullable=False,
    )
    property_set_external_id = Column(String(255), nullable=False)
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
        UniqueConstraint(
            "external_id",
            "stakeholder_key",
            name="_property_metadata_external_id_stakeholder_key_uc",
        ),
    )


class PropertySetOrm(Base):
    __tablename__ = "property_set"
    id: UUIDType = Column(
        UUIDType(binary=False),
        primary_key=True,
        nullable=False,
        default=uuid4,
    )
    external_id = Column(String(255), nullable=False)
    stakeholder_key = Column(String(36), nullable=False)
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

    __table_args__ = (
        UniqueConstraint("name", name="_property_set_name_uc"),
        UniqueConstraint(
            "external_id",
            "stakeholder_key",
            name="_property_set_external_id_stakeholder_key_uc",
        ),
    )

    @validates("property_set_type")
    def validate_property_set_type(self, key: str, value: str) -> str:  # noqa: ARG002
        valid_types = ["INTERNAL", "EXTERNAL"]
        if value not in valid_types:
            raise ValueError(f"Invalid value for {key}: {value}")
        return value
