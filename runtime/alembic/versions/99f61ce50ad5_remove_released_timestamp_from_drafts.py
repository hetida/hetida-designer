"""remove released timestamp from drafts

Revision ID: 99f61ce50ad5
Revises: 7bd371c84b25
Create Date: 2023-11-24 10:06:25.437487

"""
from sqlalchemy import orm, select, update

from alembic import op
from hetdesrun.persistence.dbmodels import TransformationRevisionDBModel
from hetdesrun.utils import State



# revision identifiers, used by Alembic.
revision = '99f61ce50ad5'
down_revision = '7bd371c84b25'
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


def downgrade():
    pass
