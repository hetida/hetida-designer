from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    ForeignKey,
    Index,
    MetaData,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy_utils import UUIDType

metadata = MetaData()


class Base(DeclarativeBase):
    metadata = metadata


# Association table between ThingNode and Source
thingnode_source_association = Table(
    "structure_thingnode_source_association",
    Base.metadata,
    Column(
        "thingnode_id",
        UUIDType(binary=False),
        ForeignKey("structure_thing_node.id"),
        primary_key=True,
    ),
    Column(
        "source_id", UUIDType(binary=False), ForeignKey("structure_source.id"), primary_key=True
    ),
)

# Association table between ThingNode and Sink
thingnode_sink_association = Table(
    "structure_thingnode_sink_association",
    Base.metadata,
    Column(
        "thingnode_id",
        UUIDType(binary=False),
        ForeignKey("structure_thing_node.id"),
        primary_key=True,
    ),
    Column("sink_id", UUIDType(binary=False), ForeignKey("structure_sink.id"), primary_key=True),
)


# ORM model for ElementType
class StructureServiceElementTypeDBModel(Base):
    __tablename__ = "structure_element_type"
    id: Mapped[UUIDType] = mapped_column(
        UUIDType(binary=False),
        primary_key=True,  # Primary key for unique identification
        nullable=False,
        default=uuid4,
    )
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    stakeholder_key: Mapped[str] = mapped_column(String(36), nullable=False)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    thing_nodes: Mapped[list["StructureServiceThingNodeDBModel"]] = relationship(
        "StructureServiceThingNodeDBModel",
        back_populates="element_type",
        # 'back_populates' specifies reciprocal relationship in
        # StructureServiceThingNodeDBModel
        cascade_backrefs=False,
        # Disable cascade_backrefs to prevent automatic session merging of related objects,
        # avoiding unintended side effects and deprecation warnings in SQLAlchemy 2.0.
    )

    # Constraints and Indexes for optimized search and uniqueness
    __table_args__ = (
        UniqueConstraint("name", name="_element_type_name_uc"),  # Enforces unique names
        UniqueConstraint(
            "external_id",
            "stakeholder_key",
            name="_element_type_external_id_stakeholder_key_uc",
        ),
        Index(
            "idx_element_type_stakeholder_external",  # Optimized search on stakeholder_key and external_id  # noqa: E501
            "stakeholder_key",
            "external_id",
        ),
    )


# ORM model for Source
class StructureServiceSourceDBModel(Base):
    __tablename__ = "structure_source"
    id: Mapped[UUIDType] = mapped_column(UUIDType(binary=False), primary_key=True, default=uuid4)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    stakeholder_key: Mapped[str] = mapped_column(String(36), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    type: Mapped[str] = mapped_column(String(255), nullable=False)
    visible: Mapped[bool] = mapped_column(Boolean, default=True)
    display_path: Mapped[str] = mapped_column(String(255), nullable=False)
    adapter_key: Mapped[str] = mapped_column(String(255), nullable=False)
    source_id: Mapped[str] = mapped_column(String(255), nullable=False)
    ref_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ref_id: Mapped[str] = mapped_column(String(255), nullable=False)
    meta_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    preset_filters: Mapped[dict] = mapped_column(JSON, nullable=False)
    passthrough_filters: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    thing_node_external_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    # Defines Many-to-Many relationship with StructureServiceThingNodeDBModel
    thing_nodes: Mapped[list["StructureServiceThingNodeDBModel"]] = relationship(
        "StructureServiceThingNodeDBModel",
        # Association table for Many-to-Many relation:
        secondary=thingnode_source_association,
        back_populates="sources",
        # 'back_populates' specifies reciprocal relationship in
        # StructureServiceThingNodeDBModel
        cascade_backrefs=False,
        # Disable cascade_backrefs to prevent automatic session merging of related objects,
        # avoiding unintended side effects and deprecation warnings in SQLAlchemy 2.0.
    )  # type: ignore

    __table_args__ = (
        UniqueConstraint(
            "external_id",
            "stakeholder_key",
            name="_source_external_id_stakeholder_key_uc",
        ),
        Index(
            "idx_source_stakeholder_external",
            "stakeholder_key",
            "external_id",
        ),
    )


# ORM model for Sink
class StructureServiceSinkDBModel(Base):
    __tablename__ = "structure_sink"
    id: Mapped[UUIDType] = mapped_column(UUIDType(binary=False), primary_key=True, default=uuid4)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    stakeholder_key: Mapped[str] = mapped_column(String(36), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    type: Mapped[str] = mapped_column(String(255), nullable=False)
    visible: Mapped[bool] = mapped_column(Boolean, default=True)
    display_path: Mapped[str] = mapped_column(String(255), nullable=False)
    adapter_key: Mapped[str] = mapped_column(String(255), nullable=False)
    sink_id: Mapped[str] = mapped_column(String(255), nullable=False)
    ref_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ref_id: Mapped[str] = mapped_column(String(255), nullable=False)
    meta_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    preset_filters: Mapped[dict] = mapped_column(JSON, nullable=False)
    passthrough_filters: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    thing_node_external_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    # Defines Many-to-Many relationship with StructureServiceThingNodeDBModel
    thing_nodes: Mapped[list["StructureServiceThingNodeDBModel"]] = relationship(
        "StructureServiceThingNodeDBModel",
        # Association table for Many-to-Many relation:
        secondary=thingnode_sink_association,
        back_populates="sinks",
        # 'back_populates' specifies reciprocal relationship in
        # StructureServiceThingNodeDBModel
        cascade_backrefs=False,
        # Disable cascade_backrefs to prevent automatic session merging of related objects,
        # avoiding unintended side effects and deprecation warnings in SQLAlchemy 2.0.
    )  # type: ignore

    __table_args__ = (
        UniqueConstraint(
            "external_id",
            "stakeholder_key",
            name="_sink_external_id_stakeholder_key_uc",
        ),
        Index(
            "idx_sink_stakeholder_external",
            "stakeholder_key",
            "external_id",
        ),
    )


# ORM model for ThingNode
class StructureServiceThingNodeDBModel(Base):
    __tablename__ = "structure_thing_node"
    id: Mapped[UUIDType] = mapped_column(UUIDType(binary=False), primary_key=True, default=uuid4)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    stakeholder_key: Mapped[str] = mapped_column(String(36), nullable=False)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    parent_node_id: Mapped[UUIDType | None] = mapped_column(
        UUIDType(binary=False), ForeignKey("structure_thing_node.id"), nullable=True
    )
    parent_external_node_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    element_type_id: Mapped[UUIDType] = mapped_column(
        UUIDType(binary=False),
        ForeignKey("structure_element_type.id"),
        nullable=False,
    )
    element_type_external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    meta_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    element_type: Mapped["StructureServiceElementTypeDBModel"] = relationship(
        "StructureServiceElementTypeDBModel", back_populates="thing_nodes", uselist=False
    )

    # Defines Many-to-Many relationship with StructureServiceSourceDBModel
    sources: Mapped[list["StructureServiceSourceDBModel"]] = relationship(
        "StructureServiceSourceDBModel",
        # Association table for Many-to-Many relation:
        secondary=thingnode_source_association,
        back_populates="thing_nodes",
        # 'back_populates' specifies reciprocal relationship in
        # StructureServiceSourceDBModel
        cascade_backrefs=False,
        # Disable cascade_backrefs to prevent automatic session merging of related objects,
        # avoiding unintended side effects and deprecation warnings in SQLAlchemy 2.0.
    )

    # Defines Many-to-Many relationship with StructureServiceSinkDBModel
    sinks: Mapped[list["StructureServiceSinkDBModel"]] = relationship(
        "StructureServiceSinkDBModel",
        # Association table for Many-to-Many relation:
        secondary=thingnode_sink_association,
        back_populates="thing_nodes",
        # 'back_populates' specifies reciprocal relationship in
        # StructureServiceSinkDBModel
        cascade_backrefs=False,
        # Disable cascade_backrefs to prevent automatic session merging of related objects,
        # avoiding unintended side effects and deprecation warnings in SQLAlchemy 2.0.
    )

    # Constraints and Indexes for optimized search and uniqueness
    __table_args__ = (
        UniqueConstraint("name", name="_thing_node_name_uc"),  # Enforces unique names
        UniqueConstraint(
            "external_id",
            "stakeholder_key",
            name="_thing_node_external_id_stakeholder_key_uc",
        ),
        Index(
            "idx_thing_node_stakeholder_external",  # Optimized search on stakeholder_key and external_id  # noqa: E501
            "stakeholder_key",
            "external_id",
        ),
    )
