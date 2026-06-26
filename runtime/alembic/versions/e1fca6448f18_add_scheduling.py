"""add scheduling
Revision ID: e1fca6448f18
Revises: 5cfafc3cf470
Create Date: 2026-02-18 17:12:45.493444
"""

import sqlalchemy as sa
import sqlalchemy_utils

from alembic import op

revision = "e1fca6448f18"
down_revision = "5cfafc3cf470"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "schedules",
        sa.Column("id", sqlalchemy_utils.types.uuid.UUIDType(binary=False), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("cron_expression", sa.String(), nullable=False),
        sa.Column(
            "transformation_id", sqlalchemy_utils.types.uuid.UUIDType(binary=False), nullable=True
        ),
        sa.Column("wiring", sa.JSON(none_as_null=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    trafo_state_enum = sa.Enum(
        "DRAFT", "RELEASED", "DISABLED", name="trafo_revision_state", create_type=False
    )
    trafo_type_enum = sa.Enum(
        "COMPONENT", "WORKFLOW", name="trafo_revision_type", create_type=False
    )

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
            trafo_state_enum,
            nullable=True,
        ),
        sa.Column(
            "transformation_type",
            trafo_type_enum,
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
    # Note: trafo_revision_state and trafo_revision_type are intentionally left
    # alone here since they predate this migration and may be used elsewhere.
