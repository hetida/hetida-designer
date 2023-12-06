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
request and their execution will fail.
The affected workflows are automatically repaired by this migration script.
"""

from copy import deepcopy

from sqlalchemy import orm, select, update

from alembic import op
from hetdesrun.persistence.dbmodels import TransformationRevisionDBModel
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

        for db_model in results:
            applicable = False
            updated_workflow_content = None
            if (
                db_model.workflow_content is not None
                and len(db_model.workflow_content["outputs"]) != 0
            ):
                updated_workflow_content = deepcopy(db_model.workflow_content)
                for output in updated_workflow_content["outputs"]:
                    if output["connector_name"] == "connector_name":
                        applicable = True
                        for operator in updated_workflow_content["operators"]:
                            if operator["id"] == output["operator_id"]:
                                for output_connector in operator["outputs"]:
                                    if output_connector["id"] == output["connector_id"]:
                                        output["connector_name"] = output_connector[
                                            "name"
                                        ]
            if applicable:
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
                        workflow_content=updated_workflow_content,
                        component_code=db_model.component_code,
                        io_interface=db_model.io_interface,
                        test_wiring=db_model.test_wiring,
                        released_timestamp=db_model.released_timestamp,
                        disabled_timestamp=db_model.disabled_timestamp,
                    )
                )


def downgrade() -> None:
    pass
