"""first migration after backend rewrite

Revision ID: 81064642674e
Revises: 
Create Date: 2022-02-21 13:42:02.394334

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision = "81064642674e"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "transformation_revisions",
        sa.Column(
            "id", sqlalchemy_utils.types.uuid.UUIDType(binary=False), nullable=False
        ),
        sa.Column(
            "revision_group_id",
            sqlalchemy_utils.types.uuid.UUIDType(binary=False),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("version_tag", sa.String(), nullable=False),
        sa.Column(
            "state",
            sa.Enum("DRAFT", "RELEASED", "DISABLED", name="trafo_revision_state"),
            nullable=False,
        ),
        sa.Column(
            "type",
            sa.Enum("COMPONENT", "WORKFLOW", name="trafo_revision_type"),
            nullable=False,
        ),
        sa.Column("documentation", sa.String(), nullable=False),
        sa.Column("workflow_content", sa.JSON(none_as_null=True), nullable=True),
        sa.Column("component_code", sa.String(), nullable=True),
        sa.Column("io_interface", sa.JSON(), nullable=False),
        sa.Column("test_wiring", sa.JSON(), nullable=False),
        sa.Column("released_timestamp", sa.DateTime(), nullable=True),
        sa.Column("disabled_timestamp", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "\n            (\n                (  (CASE WHEN component_code IS NULL THEN 0 ELSE 1 END)\n                +  (CASE WHEN workflow_content IS NULL THEN 0 ELSE 1 END)\n                ) = 1\n            )\n            ",
            name="_exactly_one_of_component_code_or_workflow_content_null_cc",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "revision_group_id",
            "version_tag",
            name="_revision_group_id_plus_version_tag_uc",
        ),
    )
    op.create_table(
        "nestings",
        sa.Column(
            "workflow_id",
            sqlalchemy_utils.types.uuid.UUIDType(binary=False),
            nullable=False,
        ),
        sa.Column(
            "via_transformation_id",
            sqlalchemy_utils.types.uuid.UUIDType(binary=False),
            nullable=False,
        ),
        sa.Column(
            "via_operator_id",
            sqlalchemy_utils.types.uuid.UUIDType(binary=False),
            nullable=False,
        ),
        sa.Column("depth", sa.Integer(), nullable=False),
        sa.Column(
            "nested_transformation_id",
            sqlalchemy_utils.types.uuid.UUIDType(binary=False),
            nullable=False,
        ),
        sa.Column(
            "nested_operator_id",
            sqlalchemy_utils.types.uuid.UUIDType(binary=False),
            nullable=False,
        ),
        sa.CheckConstraint(
            "\n            (\n                (  (CASE WHEN depth > 1 THEN 1 ELSE 0 END)\n                +( (CASE WHEN via_transformation_id = nested_transformation_id THEN 1 ELSE 0 END)\n                  *(CASE WHEN via_operator_id = nested_operator_id THEN 1 ELSE 0 END)\n                 )\n                ) = 1\n            )\n            ",
            name="_via_ids_equal_nested_ids_for_direct_nesting_cc",
        ),
        sa.CheckConstraint("depth > 0", name="_depth_natural_number_cc"),
        sa.ForeignKeyConstraint(
            ["nested_transformation_id"],
            ["transformation_revisions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["via_transformation_id"],
            ["transformation_revisions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["workflow_id"],
            ["transformation_revisions.id"],
        ),
        sa.PrimaryKeyConstraint(
            "workflow_id", "via_operator_id", "depth", "nested_operator_id"
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("nestings")
    op.drop_table("transformation_revisions")
    # ### end Alembic commands ###
