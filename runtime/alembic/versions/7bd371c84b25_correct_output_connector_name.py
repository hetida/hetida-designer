"""Correct output connector name

Revision ID: 7bd371c84b25
Revises: 81064642674e
Create Date: 2023-10-04 15:54:55.366910

Update the connector_name attribute of outputs to the correct value if it was incorrectly set
to the default value "connector_name". This has been caused by a faulty implementation in the
get_operator_and_connector_name function.

This function is used to transform WorklfowRevisionFrontendDto instances (previous data model)
to TransformationRevision instances (current data model). The incorrect implementation existed
from release 0.7.1 up to and including release 0.8.8.

Workflows that were updated with release 0.8.9 are not affected. Workflows that were last
updated between release 0.7.1 and 0.8.9 are no longer valid as of release 0.9.0.
Workflows that are in the DRAFT state will have their outputs disappear with the next PUT
request and their execution will fail. The affected
workflows are automatically repaired by this migration script.
"""

from sqlalchemy import orm, select

from alembic import op
from hetdesrun.persistence.dbmodels import TransformationRevisionDBModel
from hetdesrun.persistence.dbservice.revision import update_tr
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.persistence.models.workflow import WorkflowContent
from hetdesrun.utils import Type

# revision identifiers, used by Alembic.
revision = "7bd371c84b25"
down_revision = "81064642674e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    with orm.Session(bind=bind) as session:
        selection = select(TransformationRevisionDBModel).where(
            TransformationRevisionDBModel.type == Type.WORKFLOW
        )

        results = session.execute(selection).scalars().all()

        tr_list = [TransformationRevision.from_orm_model(result) for result in results]

        for tr in tr_list:
            applicable = False
            if isinstance(tr.content, WorkflowContent) and len(tr.content.outputs) != 0:
                for output in tr.content.outputs:
                    if output.connector_name == "connector_name":
                        applicable = True
                        for operator in tr.content.operators:
                            if operator.id == output.operator_id:
                                for output_connector in operator.outputs:
                                    if output_connector.id == output.connector_id:
                                        assert (  # noqa: S101
                                            output_connector.name is not None
                                        )
                                        output.connector_name = output_connector.name
            if applicable:
                update_tr(session, tr)


def downgrade() -> None:
    pass
