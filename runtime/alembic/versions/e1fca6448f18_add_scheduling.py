"""add scheduling

Revision ID: e1fca6448f18
Revises: 5cfafc3cf470
Create Date: 2026-02-18 17:12:45.493444

"""

import sqlalchemy as sa
import sqlalchemy_utils

from alembic import op

# revision identifiers, used by Alembic.
revision = "e1fca6448f18"
down_revision = "5cfafc3cf470"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "schedules",
        # ... your columns unchanged
    )

    # Create enums only if they don't exist
    trafo_revision_state = sa.Enum("DRAFT", "RELEASED", "DISABLED", name="trafo_revision_state")
    trafo_revision_type = sa.Enum("COMPONENT", "WORKFLOW", name="trafo_revision_type")
    scheduled_job_state = sa.Enum(
        "STARTED",
        "INVOCATION_ERROR",
        "EXECUTION_ERROR",
        "SKIPPED",
        "SUCCESS",
        name="scheduled_job_state",
    )

    trafo_revision_state.create(op.get_bind(), checkfirst=True)
    trafo_revision_type.create(op.get_bind(), checkfirst=True)
    scheduled_job_state.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "schedule_executions",
        sa.Column("id", sqlalchemy_utils.types.uuid.UUIDType(binary=False), nullable=False),
        sa.Column(
            "schedule_id", sqlalchemy_utils.types.uuid.UUIDType(binary=False), nullable=False
        ),
        sa.Column("last_state_update", sa.DateTime(), nullable=True),
        sa.Column("start", sa.DateTime(), nullable=True),
        sa.Column("end", sa.DateTime(), nullable=True),
        sa.Column(
            "transformation_id", sqlalchemy_utils.types.uuid.UUIDType(binary=False), nullable=False
        ),
        sa.Column("transformation_name", sa.String(), nullable=True),
        sa.Column("transformation_version_tag", sa.String(), nullable=True),
        sa.Column(
            "transformation_state",
            sa.Enum(
                "DRAFT", "RELEASED", "DISABLED", name="trafo_revision_state", create_type=False
            ),
            nullable=True,
        ),
        sa.Column(
            "transformation_type",
            sa.Enum("COMPONENT", "WORKFLOW", name="trafo_revision_type", create_type=False),
            nullable=True,
        ),
        sa.Column(
            "state",
            sa.Enum(
                "STARTED",
                "INVOCATION_ERROR",
                "EXECUTION_ERROR",
                "SKIPPED",
                "SUCCESS",
                name="scheduled_job_state",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "trafo_exec_job_id", sqlalchemy_utils.types.uuid.UUIDType(binary=False), nullable=False
        ),
        sa.Column("exec_input", sa.JSON(none_as_null=True), nullable=True),
        sa.Column("exec_result", sa.JSON(none_as_null=True), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("schedule_executions")
    op.drop_table("schedules")

    sa.Enum(name="scheduled_job_state").drop(op.get_bind(), checkfirst=True)
