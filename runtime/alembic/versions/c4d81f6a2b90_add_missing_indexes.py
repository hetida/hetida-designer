"""add missing indexes on hot-path foreign key / lookup columns

Revision ID: c4d81f6a2b90
Revises: e1fca6448f18
Create Date: 2026-07-14

Adds indexes that the ORM models rely on but which were missing from the migrated schema.
All three columns are non-leading, unindexed columns that are filtered on hot paths (and
foreign keys are not auto-indexed by postgres):

* nestings.nested_transformation_id -- filtered by find_all_nestings (deprecation
  propagation, is_unused / filter_unused, get_all_nested_transformation_revisions during
  execution)
* schedule_executions.(schedule_id, last_state_update) -- the "latest execution for a
  schedule" lookup (filter schedule_id, order by last_state_update desc) on a table that
  grows with every scheduled run
* structure_thing_node.parent_node_id -- filtered on every structure-tree expansion
  (get_children)

Note: the structure_* tables live in a separate MetaData that alembic autogenerate does
not track, so their index is created here explicitly.
"""

from alembic import op

revision = "c4d81f6a2b90"
down_revision = "e1fca6448f18"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "ix_nestings_nested_transformation_id",
        "nestings",
        ["nested_transformation_id"],
    )
    op.create_index(
        "ix_schedule_executions_schedule_id_last_state_update",
        "schedule_executions",
        ["schedule_id", "last_state_update"],
    )
    op.create_index(
        "ix_structure_thing_node_parent_node_id",
        "structure_thing_node",
        ["parent_node_id"],
    )


def downgrade():
    op.drop_index("ix_structure_thing_node_parent_node_id", table_name="structure_thing_node")
    op.drop_index(
        "ix_schedule_executions_schedule_id_last_state_update",
        table_name="schedule_executions",
    )
    op.drop_index("ix_nestings_nested_transformation_id", table_name="nestings")
