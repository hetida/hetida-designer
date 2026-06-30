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

    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # Unfortunately sqlalchemy up to 2.0 is not capable of handling creation of
    # sa.Enum types well. It only works well if you use the explicit postgres dialect
    # Enum type. But if you want to stay compatible with both sqlite and postgres and
    # use sa.Enum the following happens, if the same such type (same name) is used
    # more than one time in different tables created in different migrations:
    # * On sqlite: it works, since sqlalchemy will just create String columns and
    #   not create a type, since it has no proper Enum type
    # * On postgres:
    #   * it works if all migrations are run at once (in the same transaction). It
    #     figures out that the type only needs to be created once.
    #   * If migrations run separately (as is in a true upgrade) you get a "Duplicate"
    #     error since it tries to create the type a second time and its already there.
    #     It does not help to set "create_type" keyword of sa.Enum to False: This will
    #     be ignored when passed down to the actual implementation. See
    #     https://github.com/sqlalchemy/sqlalchemy/issues/10604
    #     it will be eventually fixed in sqlalchemy 2.1
    # Therefore, unfortunately we need to explicitely distinguish databases here, since
    # we want to keep compatibility for now.

    if is_postgres:
        # On Postgres, use the pre-existing enum types by name via USING cast.
        # sa.String() creates the column, then we alter its type to the existing enum.
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
                "transformation_id",
                sqlalchemy_utils.types.uuid.UUIDType(binary=False),
                nullable=False,
            ),
            sa.Column("transformation_name", sa.String(), nullable=True),
            sa.Column("transformation_version_tag", sa.String(), nullable=True),
            sa.Column("transformation_state", sa.String(), nullable=True),  # altered below
            sa.Column("transformation_type", sa.String(), nullable=True),  # altered below
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
                "trafo_exec_job_id",
                sqlalchemy_utils.types.uuid.UUIDType(binary=False),
                nullable=False,
            ),
            sa.Column("exec_input", sa.JSON(none_as_null=True), nullable=True),
            sa.Column("exec_result", sa.JSON(none_as_null=True), nullable=True),
            sa.Column("error_message", sa.String(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        # Now cast the String columns to the pre-existing Postgres enum types.
        op.execute(
            "ALTER TABLE schedule_executions "
            "ALTER COLUMN transformation_state TYPE trafo_revision_state "
            "USING transformation_state::trafo_revision_state"
        )
        op.execute(
            "ALTER TABLE schedule_executions "
            "ALTER COLUMN transformation_type TYPE trafo_revision_type "
            "USING transformation_type::trafo_revision_type"
        )
    else:
        # SQLite has no native enum types => String typed column
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
                "transformation_id",
                sqlalchemy_utils.types.uuid.UUIDType(binary=False),
                nullable=False,
            ),
            sa.Column("transformation_name", sa.String(), nullable=True),
            sa.Column("transformation_version_tag", sa.String(), nullable=True),
            sa.Column("transformation_state", sa.String(), nullable=True),
            sa.Column("transformation_type", sa.String(), nullable=True),
            sa.Column(
                "state",
                sa.Enum(
                    "STARTED",
                    "INVOCATION_ERROR",
                    "EXECUTION_ERROR",
                    "SKIPPED",
                    "SUCCESS",
                    name="scheduled_job_state",
                    create_constraint=True,
                ),
                nullable=False,
            ),
            sa.Column(
                "trafo_exec_job_id",
                sqlalchemy_utils.types.uuid.UUIDType(binary=False),
                nullable=False,
            ),
            sa.Column("exec_input", sa.JSON(none_as_null=True), nullable=True),
            sa.Column("exec_result", sa.JSON(none_as_null=True), nullable=True),
            sa.Column("error_message", sa.String(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )


def downgrade():
    op.drop_table("schedule_executions")
    op.drop_table("schedules")
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        sa.Enum(name="scheduled_job_state").drop(bind, checkfirst=True)
    # trafo_revision_state and trafo_revision_type predate this migration — leave them alone.
