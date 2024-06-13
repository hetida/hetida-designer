from typing import NamedTuple, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, backref, declarative_base, relationship, validates
from sqlalchemy_utils import UUIDType

from hetdesrun.utils import State, Type

Base = declarative_base()


class TransformationRevisionDBModel(Base):
    __tablename__ = "transformation_revisions"

    id: UUIDType = Column(  # noqa: A003
        UUIDType(binary=False), primary_key=True, default=uuid4
    )
    revision_group_id: UUIDType = Column(
        UUIDType(binary=False), default=uuid4, nullable=False
    )
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    category = Column(String, nullable=False)
    version_tag = Column(String, nullable=False)
    state = Column(Enum(State), nullable=False)
    type = Column(Enum(Type), nullable=False)  # noqa: A003
    documentation = Column(String, nullable=False)
    workflow_content = Column(
        JSON(none_as_null=True), nullable=True, default=lambda: None
    )
    component_code = Column(String, nullable=True)
    io_interface = Column(JSON, nullable=False)
    test_wiring = Column(JSON, nullable=False)
    released_timestamp = Column(DateTime, nullable=True)
    disabled_timestamp = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "revision_group_id",
            "version_tag",
            name="_revision_group_id_plus_version_tag_uc",
        ),
        CheckConstraint(
            """
            (
                (  (CASE WHEN component_code IS NULL THEN 0 ELSE 1 END)
                +  (CASE WHEN workflow_content IS NULL THEN 0 ELSE 1 END)
                ) = 1
            )
            """,
            name="_exactly_one_of_component_code_or_workflow_content_null_cc",
        ),
    )


class NestingDBModel(Base):
    __tablename__ = "nestings"

    workflow_id: UUIDType = Column(
        UUIDType(binary=False),
        ForeignKey(TransformationRevisionDBModel.id),
        primary_key=True,
        default=uuid4,
    )
    via_transformation_id: UUIDType = Column(
        UUIDType(binary=False),
        ForeignKey(TransformationRevisionDBModel.id),
        default=uuid4,
        nullable=False,
    )
    via_operator_id: UUIDType = Column(
        UUIDType(binary=False),
        primary_key=True,
        default=uuid4,
    )
    depth = Column(Integer, primary_key=True, nullable=False)
    nested_transformation_id: UUIDType = Column(
        UUIDType(binary=False),
        ForeignKey(TransformationRevisionDBModel.id),
        default=uuid4,
        nullable=False,
    )
    nested_operator_id: UUIDType = Column(
        UUIDType(binary=False),
        primary_key=True,
        default=uuid4,
    )

    workflow: TransformationRevisionDBModel = relationship(
        TransformationRevisionDBModel,
        foreign_keys=[workflow_id],
    )
    via_transformation: TransformationRevisionDBModel = relationship(
        TransformationRevisionDBModel, foreign_keys=[via_transformation_id]
    )
    nested_transformation: TransformationRevisionDBModel = relationship(
        TransformationRevisionDBModel, foreign_keys=[nested_transformation_id]
    )

    __table_args__ = (
        CheckConstraint(
            "depth > 0",
            name="_depth_natural_number_cc",
        ),
        CheckConstraint(
            """
            (
                (  (CASE WHEN depth > 1 THEN 1 ELSE 0 END)
                +( (CASE WHEN via_transformation_id = nested_transformation_id THEN 1 ELSE 0 END)
                  *(CASE WHEN via_operator_id = nested_operator_id THEN 1 ELSE 0 END)
                 )
                ) = 1
            )
            """,
            name="_via_ids_equal_nested_ids_for_direct_nesting_cc",
        ),
    )


class Descendant(NamedTuple):
    depth: int
    transformation_id: UUID
    operator_id: UUID


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
    entity_uuid = Column(String(36), nullable=False)
    element_type: Mapped["ElementTypeOrm"] = relationship(
        "ElementTypeOrm", back_populates="thing_nodes", uselist=False
    )
    children: Mapped[list["ThingNodeOrm"]] = relationship(
        "ThingNodeOrm",
        backref=backref("parent", remote_side=[id]),
        cascade="all, delete-orphan",
    )
    sources: Mapped[list["SourceOrm"]] = relationship(
        "SourceOrm",
        back_populates="thing_node",
        cascade="all, delete-orphan",
    )
    sinks: Mapped[list["SinkOrm"]] = relationship(
        "SinkOrm",
        back_populates="thing_node",
        cascade="all, delete-orphan",
    )

    __table_args__ = (UniqueConstraint("name", name="_thing_node_name_uc"),)


class SourceOrm(Base):
    __tablename__ = "source"
    id: UUIDType = Column(
        "source_id", UUIDType(binary=False), primary_key=True, default=uuid4
    )
    thing_node_id: UUIDType = Column(
        UUIDType(binary=False), ForeignKey("thing_node.thing_node_id")
    )
    name = Column(String(255), nullable=False)
    type = Column(String, nullable=False)
    visible = Column(Boolean, default=True)
    thing_node: Mapped["ThingNodeOrm"] = relationship(
        "ThingNodeOrm", back_populates="sources"
    )


class SinkOrm(Base):
    __tablename__ = "sink"
    id: UUIDType = Column(
        "sink_id", UUIDType(binary=False), primary_key=True, default=uuid4
    )
    thing_node_id: UUIDType = Column(
        UUIDType(binary=False), ForeignKey("thing_node.thing_node_id")
    )
    name = Column(String(255), nullable=False)
    type = Column(String(255), nullable=False)
    visible = Column(Boolean, default=True)
    thing_node: Mapped["ThingNodeOrm"] = relationship(
        "ThingNodeOrm", back_populates="sinks"
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
