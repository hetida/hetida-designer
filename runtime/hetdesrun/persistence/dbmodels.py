from datetime import datetime
from typing import NamedTuple
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy_utils import UUIDType

from hetdesrun.utils import State, Type


class Base(DeclarativeBase):
    pass


class TransformationRevisionDBModel(Base):
    __tablename__ = "transformation_revisions"

    id: Mapped[UUIDType] = mapped_column(  # noqa: A003
        UUIDType(binary=False), primary_key=True, default=uuid4
    )
    revision_group_id: Mapped[UUIDType] = mapped_column(
        UUIDType(binary=False), default=uuid4, nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    version_tag: Mapped[str] = mapped_column(String, nullable=False)
    state: Mapped[State] = mapped_column(Enum(State), nullable=False)
    type: Mapped[Type] = mapped_column(Enum(Type), nullable=False)
    documentation: Mapped[str] = mapped_column(String, nullable=False)
    workflow_content: Mapped[dict | None] = mapped_column(
        JSON(none_as_null=True), nullable=True, default=lambda: None
    )
    component_code: Mapped[str | None] = mapped_column(String, nullable=True)
    io_interface: Mapped[dict] = mapped_column(JSON, nullable=False)
    test_wiring: Mapped[dict] = mapped_column(JSON, nullable=False)
    release_wiring: Mapped[dict] = mapped_column(JSON, nullable=False)
    released_timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    disabled_timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

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

    workflow_id: Mapped[UUIDType] = mapped_column(
        UUIDType(binary=False),
        ForeignKey(TransformationRevisionDBModel.id),
        primary_key=True,
        default=uuid4,
    )
    via_transformation_id: Mapped[UUIDType] = mapped_column(
        UUIDType(binary=False),
        ForeignKey(TransformationRevisionDBModel.id),
        default=uuid4,
        nullable=False,
    )
    via_operator_id: Mapped[UUIDType] = mapped_column(
        UUIDType(binary=False),
        primary_key=True,
        default=uuid4,
    )
    depth: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    nested_transformation_id: Mapped[UUIDType] = mapped_column(
        UUIDType(binary=False),
        ForeignKey(TransformationRevisionDBModel.id),
        default=uuid4,
        nullable=False,
    )
    nested_operator_id: Mapped[UUIDType] = mapped_column(
        UUIDType(binary=False),
        primary_key=True,
        default=uuid4,
    )

    workflow: Mapped[TransformationRevisionDBModel] = relationship(
        TransformationRevisionDBModel,
        foreign_keys=[workflow_id],
    )
    via_transformation: Mapped[TransformationRevisionDBModel] = relationship(
        TransformationRevisionDBModel, foreign_keys=[via_transformation_id]
    )
    nested_transformation: Mapped[TransformationRevisionDBModel] = relationship(
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
