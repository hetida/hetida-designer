from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    ForeignKey,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, declarative_base, relationship
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
    thing_nodes: list["ThingNodeOrm"] = relationship("ThingNodeOrm", back_populates="element_type")

    __table_args__ = (
        UniqueConstraint("name", name="_element_type_name_uc"),
        UniqueConstraint(
            "external_id",
            "stakeholder_key",
            name="_element_type_external_id_stakeholder_key_uc",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<ElementTypeOrm(id={self.id}, external_id={self.external_id}, "
            f"stakeholder_key={self.stakeholder_key}, "
            f"name={self.name}, description={self.description}, "
            f"thing_nodes={[thing_node.id for thing_node in self.thing_nodes]})>"
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
            f"<ThingNodeOrm(id={self.id}, external_id={self.external_id}, "
            f"stakeholder_key={self.stakeholder_key}, "
            f"name={self.name}, description={self.description}, "
            f"parent_node_id={self.parent_node_id}, "
            f"parent_external_node_id={self.parent_external_node_id}, "
            f"element_type_id={self.element_type_id}, "
            f"element_type_external_id={self.element_type_external_id}, "
            f"meta_data={self.meta_data})>"
        )


class SourceOrm(Base):
    __tablename__ = "source"
    id: UUIDType = Column(UUIDType(binary=False), primary_key=True, default=uuid4)
    external_id = Column(String(255), nullable=False)
    stakeholder_key = Column(String(36), nullable=False)
    name: str = Column(String(255), nullable=False, unique=True)
    type: str = Column(String(255), nullable=False)
    visible: bool = Column(Boolean, default=True)
    path: str = Column(String(255), nullable=False)
    adapter_key: str = Column(String(255), nullable=False)
    source_id: str = Column(String(255), nullable=False)
    meta_data: dict | None = Column(JSON, nullable=True)
    preset_filters: dict = Column(JSON, nullable=False)
    passthrough_filters: list[dict] | None = Column(JSON, nullable=True)
    thing_node_external_ids: list[str] = Column(JSON, nullable=True)

    thing_nodes: list["ThingNodeOrm"] = relationship(
        "ThingNodeOrm", secondary="thingnode_source_association"
    )

    __table_args__ = (
        UniqueConstraint(
            "external_id",
            "stakeholder_key",
            name="_source_external_id_stakeholder_key_uc",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<SourceOrm(id={self.id}, external_id={self.external_id}, "
            f"stakeholder_key={self.stakeholder_key}, "
            f"name={self.name}, type={self.type}, visible={self.visible}, "
            f"path={self.path}, "
            f"adapter_key={self.adapter_key}, "
            f"source_id={self.source_id}, meta_data={self.meta_data}, "
            f"preset_filters={self.preset_filters}, "
            f"passthrough_filters={self.passthrough_filters}, "
            f"thing_nodes={[thing_node.id for thing_node in self.thing_nodes]})>"
        )


class SinkOrm(Base):
    __tablename__ = "sink"

    id: UUIDType = Column(UUIDType(binary=False), primary_key=True, default=uuid4)
    external_id = Column(String(255), nullable=False)
    stakeholder_key = Column(String(36), nullable=False)
    name: str = Column(String(255), nullable=False, unique=True)
    type: str = Column(String(255), nullable=False)
    visible: bool = Column(Boolean, default=True)
    path: str = Column(String(255), nullable=False)
    adapter_key: str = Column(String(255), nullable=False)
    sink_id: str = Column(String(255), nullable=False)
    meta_data: dict | None = Column(JSON, nullable=True)
    preset_filters: dict = Column(JSON, nullable=False)
    passthrough_filters: list[dict] | None = Column(JSON, nullable=True)
    thing_node_external_ids: list[str] = Column(JSON, nullable=True)

    thing_nodes: list["ThingNodeOrm"] = relationship(
        "ThingNodeOrm", secondary="thingnode_sink_association"
    )

    __table_args__ = (
        UniqueConstraint(
            "external_id",
            "stakeholder_key",
            name="_sink_external_id_stakeholder_key_uc",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<SinkOrm(id={self.id}, external_id={self.external_id}, "
            f"stakeholder_key={self.stakeholder_key}, "
            f"name={self.name}, type={self.type}, visible={self.visible}, "
            f"path={self.path}, "
            f"adapter_key={self.adapter_key}, "
            f"sink_id={self.sink_id}, meta_data={self.meta_data}, "
            f"preset_filters={self.preset_filters}, "
            f"passthrough_filters={self.passthrough_filters}, "
            f"thing_nodes={[thing_node.id for thing_node in self.thing_nodes]})>"
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
