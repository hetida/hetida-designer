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

from sqlalchemy import orm, select, update

from alembic import op
from hetdesrun.persistence.dbmodels import TransformationRevisionDBModel
from hetdesrun.utils import State

# revision identifiers, used by Alembic.
revision = "99f61ce50ad5"
down_revision = "7bd371c84b25"
branch_labels = None
depends_on = None


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
