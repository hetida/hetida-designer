"""remove released timestamp from drafts

Revision ID: 99f61ce50ad5
Revises: 7bd371c84b25
Create Date: 2023-11-24 10:06:25.437487

"""
from sqlalchemy import orm, select

from alembic import op
from hetdesrun.persistence.dbmodels import TransformationRevisionDBModel
from hetdesrun.persistence.dbservice.revision import update_tr
from hetdesrun.persistence.models.transformation import TransformationRevision
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

        for orm_model in results:
            if orm_model.released_timestamp is not None:
                orm_model.released_timestamp = None
                update_tr(session, TransformationRevision.from_orm_model(orm_model))


def downgrade():
    pass
