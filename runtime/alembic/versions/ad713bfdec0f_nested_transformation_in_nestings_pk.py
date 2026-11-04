"""add nested_transformation_id to the primary key of nestings and recompute nestings

Revision ID: ad713bfdec0f
Revises: c4d81f6a2b90
Create Date: 2026-11-04

The nestings of a workflow are derived from those of the workflows it contains directly,
which do not record the path below their own operators. So two nestings of a workflow may
differ only in their nested transformation revision: New revisions and copies of a
workflow keep the operator ids, upgrading an operator keeps its id as well. If a workflow
contains two revisions of a workflow in which an operator refers to different
transformation revisions, e.g. after upgrading it in one of them, a workflow containing
the former has nestings via the same operator, at the same depth and with the same nested
operator, but with different nested transformation revisions.

With the previous primary key (workflow_id, via_operator_id, depth, nested_operator_id)
only one of them could be stored. Up to release 0.14.0 the others were lost silently, since
then storing such workflows failed. A missing nesting lets the execution of the workflow
fail, since the nested transformation revision is not loaded, and the workflow is missing
when determining the workflows containing that transformation revision or when passing on
its deprecation.

The lost nestings cannot be told from the remaining ones, so this migration recomputes all
nestings of depth > 1 from those of depth 1, which are complete, as storing all workflows
again from the innermost to the outermost would. This also brings the nestings of workflows
containing DRAFT workflows up to date which changed since the containing workflow was
stored the last time.
"""

import logging
from collections import defaultdict
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy_utils import UUIDType

from alembic import op

# revision identifiers, used by Alembic.
revision = "ad713bfdec0f"
down_revision = "c4d81f6a2b90"
branch_labels = None
depends_on = None

logger = logging.getLogger("hetdesrun")

PREVIOUS_PRIMARY_KEY = ["workflow_id", "via_operator_id", "depth", "nested_operator_id"]
PRIMARY_KEY = [
    "workflow_id",
    "via_operator_id",
    "depth",
    "nested_transformation_id",
    "nested_operator_id",
]

nestings = sa.table(
    "nestings",
    sa.column("workflow_id", UUIDType(binary=False)),
    sa.column("via_transformation_id", UUIDType(binary=False)),
    sa.column("via_operator_id", UUIDType(binary=False)),
    sa.column("depth", sa.Integer()),
    sa.column("nested_transformation_id", UUIDType(binary=False)),
    sa.column("nested_operator_id", UUIDType(binary=False)),
)


def replace_primary_key(columns: list[str]) -> None:
    # SQLite cannot alter constraints, so the batch mode recreates the table there. Its
    # primary key created by the first migration is unnamed in SQLite, the naming convention
    # gives it the name it has in postgres.
    with op.batch_alter_table("nestings", naming_convention={"pk": "nestings_pkey"}) as batch_op:
        batch_op.drop_constraint("nestings_pkey", type_="primary")
        batch_op.create_primary_key("nestings_pkey", columns)


def recompute_indirect_nestings() -> None:
    bind = op.get_bind()

    # operator id and transformation revision id of the direct operators of each workflow
    operators_by_workflow_id: dict[UUID, list[tuple[UUID, UUID]]] = defaultdict(list)
    for row in bind.execute(
        sa.select(
            nestings.c.workflow_id,
            nestings.c.nested_operator_id,
            nestings.c.nested_transformation_id,
        ).where(nestings.c.depth == 1)
    ):
        operators_by_workflow_id[row.workflow_id].append(
            (row.nested_operator_id, row.nested_transformation_id)
        )

    descendants_by_workflow_id: dict[UUID, set[tuple[int, UUID, UUID]]] = {}

    def descendants(workflow_id: UUID) -> set[tuple[int, UUID, UUID]]:
        """Depth, transformation revision id and operator id of all nested operators"""
        if workflow_id not in descendants_by_workflow_id:
            result = set()
            for operator_id, transformation_id in operators_by_workflow_id.get(workflow_id, []):
                result.add((1, transformation_id, operator_id))
                result.update(
                    (depth + 1, *descendant)
                    for depth, *descendant in descendants(transformation_id)
                )
            descendants_by_workflow_id[workflow_id] = result
        return descendants_by_workflow_id[workflow_id]

    # values in the order of the columns of nestings
    indirect_nestings = {
        (workflow_id, via_transformation_id, via_operator_id, depth + 1, *descendant)
        for workflow_id, operators in operators_by_workflow_id.items()
        for via_operator_id, via_transformation_id in operators
        for depth, *descendant in descendants(via_transformation_id)
    }
    previous_indirect_nestings = {
        tuple(row) for row in bind.execute(sa.select(nestings).where(nestings.c.depth > 1))
    }

    bind.execute(sa.delete(nestings).where(nestings.c.depth > 1))
    if len(indirect_nestings) > 0:
        bind.execute(
            sa.insert(nestings),
            [dict(zip(nestings.c.keys(), nesting, strict=True)) for nesting in indirect_nestings],
        )

    logger.info(
        "Recomputed %i nestings of depth > 1: %i added, %i removed",
        len(indirect_nestings),
        len(indirect_nestings - previous_indirect_nestings),
        len(previous_indirect_nestings - indirect_nestings),
    )


def upgrade() -> None:
    replace_primary_key(PRIMARY_KEY)
    recompute_indirect_nestings()


def downgrade() -> None:
    # The previous primary key admits only one of the nestings which differ only in their
    # nested transformation revision.
    other = nestings.alias("other")
    op.get_bind().execute(
        sa.delete(nestings).where(
            sa.exists().where(
                other.c.workflow_id == nestings.c.workflow_id,
                other.c.via_operator_id == nestings.c.via_operator_id,
                other.c.depth == nestings.c.depth,
                other.c.nested_operator_id == nestings.c.nested_operator_id,
                other.c.nested_transformation_id < nestings.c.nested_transformation_id,
            )
        )
    )
    replace_primary_key(PREVIOUS_PRIMARY_KEY)
