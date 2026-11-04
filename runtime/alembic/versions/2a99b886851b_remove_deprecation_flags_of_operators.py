"""remove the deprecation flags of operators from the stored workflows

Revision ID: 2a99b886851b
Revises: ad713bfdec0f
Create Date: 2026-11-04

An operator stores the state of the transformation revision it instantiates as it was when
instantiating it, DRAFT or RELEASED. Up to now, deprecating a transformation revision set the
state of the operators instantiating it or a workflow containing it to DISABLED in all
workflows containing it, also in released ones, and storing a workflow set it for operators
instantiating a deprecated transformation revision. These flags were never removed, e.g.
when a DRAFT workflow no longer contains the deprecated transformation revision, and
importing a released workflow without overwriting released ones failed if they differed.

Now these flags are determined from the nestings when providing workflows, e.g. to the
frontend, and storing a workflow replaces them. Like that, this migration replaces the
stored DISABLED states of operators by the state of the transformation revision they
instantiate, DRAFT or otherwise RELEASED.
"""

import logging
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy_utils import UUIDType

from alembic import op

# revision identifiers, used by Alembic.
revision = "2a99b886851b"
down_revision = "ad713bfdec0f"
branch_labels = None
depends_on = None

logger = logging.getLogger("hetdesrun")

transformation_revisions = sa.table(
    "transformation_revisions",
    sa.column("id", UUIDType(binary=False)),
    # an enum in postgres, compared in Python only
    sa.column("state", sa.String()),
    sa.column("workflow_content", sa.JSON()),
)


def upgrade() -> None:
    bind = op.get_bind()
    states = {
        row.id: row.state
        for row in bind.execute(
            sa.select(transformation_revisions.c.id, transformation_revisions.c.state)
        )
    }

    updated_workflows = 0
    for workflow_id, content in bind.execute(
        sa.select(transformation_revisions.c.id, transformation_revisions.c.workflow_content)
    ).all():
        if content is None:
            continue
        flagged_operators = [
            operator for operator in content["operators"] if operator["state"] == "DISABLED"
        ]
        if len(flagged_operators) == 0:
            continue
        # names as WorkflowContent.operator_names_represent_state
        for operator in flagged_operators:
            if states.get(UUID(operator["transformation_id"])) == "DRAFT":
                operator["state"] = "DRAFT"
                if not operator["name"].startswith("(DRAFT) "):
                    operator["name"] = "(DRAFT) " + operator["name"]
            else:
                operator["state"] = "RELEASED"
                operator["name"] = operator["name"].removeprefix("(DRAFT) ")
        bind.execute(
            sa.update(transformation_revisions)
            .where(transformation_revisions.c.id == workflow_id)
            .values(workflow_content=content)
        )
        updated_workflows += 1

    logger.info("Removed the deprecation flags of operators from %i workflows", updated_workflows)


def downgrade() -> None:
    # The flags are not restored. Previous versions set them when deprecating a
    # transformation revision and when storing a workflow.
    pass
