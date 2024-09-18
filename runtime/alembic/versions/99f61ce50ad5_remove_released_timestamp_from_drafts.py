"""Remove released timestamp from drafts

Revision ID: 99f61ce50ad5
Revises: 7bd371c84b25
Create Date: 2023-11-24 10:06:25.437487

Remove the released_timestamp attribute from transformation revisions that are in the DRAFT state,
because from revision 0.9.4, DRAFT transformation revisions with a released_timestamp cause a
ValidationError.

Such transformation revisions are caused by an error in the frontend implementation, where the
released_timestamp was copied from the original transformation revision when copying a
transformation revision or creating a new revision.
The incorrect implementation existed in release 0.8.9.

Draft workflows and components that were updated with release 0.9.0 up to and including release
0.9.3 are not affected, since the backend removed the released_timestamp from DRAFT
transformation revisions as part of their validation.
The affected workflows are automatically repaired by this migration script.
"""

from uuid import UUID, uuid4


from sqlalchemy import (
    orm,
    select,
    update,
    JSON,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy_utils import UUIDType
from sqlalchemy.orm import declarative_base


from alembic import op
from hetdesrun.utils import State, Type

# revision identifiers, used by Alembic.
revision = "99f61ce50ad5"
down_revision = "7bd371c84b25"
branch_labels = None
depends_on = None

Base = declarative_base()


class TransformationRevisionDBModel(Base):
    __tablename__ = "transformation_revisions"

    id: UUIDType = Column(  # noqa: A003
        UUIDType(binary=False), primary_key=True, default=uuid4
    )
    revision_group_id: UUIDType = Column(UUIDType(binary=False), default=uuid4, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    category = Column(String, nullable=False)
    version_tag = Column(String, nullable=False)
    state = Column(Enum(State), nullable=False)
    type = Column(Enum(Type), nullable=False)  # noqa: A003
    documentation = Column(String, nullable=False)
    workflow_content = Column(JSON(none_as_null=True), nullable=True, default=lambda: None)
    component_code = Column(String, nullable=True)
    io_interface = Column(JSON, nullable=False)
    test_wiring = Column(JSON, nullable=False)
    released_timestamp = Column(DateTime, nullable=True, default=lambda: None)
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


def upgrade() -> None:
    bind = op.get_bind()

    with orm.Session(bind=bind) as session:
        selection = select(TransformationRevisionDBModel).where(
            TransformationRevisionDBModel.state == State.DRAFT
        )

        results = session.execute(selection).scalars().all()

        for db_model in results:
            if db_model.released_timestamp is not None:
                session.execute(
                    update(TransformationRevisionDBModel)
                    .where(TransformationRevisionDBModel.id == db_model.id)
                    .values(
                        revision_group_id=db_model.revision_group_id,
                        name=db_model.name,
                        description=db_model.description,
                        category=db_model.category,
                        version_tag=db_model.version_tag,
                        state=db_model.state,
                        type=db_model.type,
                        documentation=db_model.documentation,
                        workflow_content=db_model.workflow_content,
                        component_code=db_model.component_code,
                        io_interface=db_model.io_interface,
                        test_wiring=db_model.test_wiring,
                        released_timestamp=None,
                        disabled_timestamp=db_model.disabled_timestamp,
                    )
                )


def downgrade() -> None:
    pass
