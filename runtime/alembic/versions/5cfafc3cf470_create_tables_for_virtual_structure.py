"""create_tables_for_virtual_structure

Revision ID: 5cfafc3cf470
Revises: 99f61ce50ad5
Create Date: 2024-07-04 11:54:37.172484

"""

import sqlalchemy as sa
from sqlalchemy_utils import UUIDType

from alembic import op

# revision identifiers, used by Alembic.
revision = "5cfafc3cf470"
down_revision = "99f61ce50ad5"
branch_labels = None
depends_on = None


def upgrade():
    # Create table element_type
    op.create_table(
        "element_type",
        sa.Column(
            "id",
            UUIDType(binary=False),
            primary_key=True,
            nullable=False,
            default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("icon", sa.String(length=255), nullable=True),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.UniqueConstraint("name", name="_element_type_name_uc"),
    )

    # Create table property_set
    op.create_table(
        "property_set",
        sa.Column(
            "id",
            UUIDType(binary=False),
            primary_key=True,
            nullable=False,
            default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.Column(
            "reference_table_name", sa.String(length=100), unique=True, nullable=False
        ),
        sa.Column("property_set_type", sa.String(length=50), nullable=False),
        sa.UniqueConstraint("name", name="_property_set_name_uc"),
    )

    # Create table property_metadata
    op.create_table(
        "property_metadata",
        sa.Column(
            "id",
            UUIDType(binary=False),
            primary_key=True,
            nullable=False,
            default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "property_set_id",
            UUIDType(binary=False),
            sa.ForeignKey("property_set.id"),
            nullable=False,
        ),
        sa.Column("column_name", sa.String(length=255), nullable=False),
        sa.Column("column_label", sa.String(length=255), nullable=False),
        sa.Column(
            "column_type",
            sa.Enum("STRING", "INT", "FLOAT", "BOOLEAN", name="column_type"),
            nullable=True,
        ),
        sa.Column("field_length", sa.Integer(), nullable=True),
        sa.Column("nullable", sa.Boolean(), nullable=False, default=True),
        sa.Column("order_no", sa.Integer(), nullable=False),
        sa.CheckConstraint("field_length > 0", name="_field_length_positive_ck"),
        sa.UniqueConstraint("property_set_id", name="_property_metadata_psid_uc"),
    )

    # Create table thing_node
    op.create_table(
        "thing_node",
        sa.Column(
            "id",
            UUIDType(binary=False),
            primary_key=True,
            nullable=False,
            default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.Column(
            "parent_node_id",
            UUIDType(binary=False),
            sa.ForeignKey("thing_node.id"),
            nullable=True,
        ),
        sa.Column(
            "element_type_id",
            UUIDType(binary=False),
            sa.ForeignKey("element_type.id"),
            nullable=False,
        ),
        sa.Column("entity_uuid", sa.String(length=36), nullable=False),
        sa.Column("meta_data", sa.JSON(), nullable=True),
        sa.UniqueConstraint("name", name="_thing_node_name_uc"),
    )

    # Create table source
    op.create_table(
        "source",
        sa.Column(
            "id",
            UUIDType(binary=False),
            primary_key=True,
            nullable=False,
            default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=255), nullable=False),
        sa.Column("visible", sa.Boolean(), default=True),
        sa.Column("adapter_key", sa.String(length=255), nullable=False),
        sa.Column("source_id", UUIDType(binary=False), nullable=False),
        sa.Column(
            "thing_node_id",
            UUIDType(binary=False),
            sa.ForeignKey("thing_node.id"),
            nullable=True,
        ),
        sa.Column("preset_filters", sa.JSON(), nullable=True),
        sa.Column("passthrough_filters", sa.JSON(), nullable=True),
    )

    # Create table sink
    op.create_table(
        "sink",
        sa.Column(
            "id",
            UUIDType(binary=False),
            primary_key=True,
            nullable=False,
            default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=255), nullable=False),
        sa.Column("visible", sa.Boolean(), default=True),
        sa.Column("adapter_key", sa.String(length=255), nullable=False),
        sa.Column("sink_id", UUIDType(binary=False), nullable=False),
        sa.Column(
            "thing_node_id",
            UUIDType(binary=False),
            sa.ForeignKey("thing_node.id"),
            nullable=True,
        ),
        sa.Column("preset_filters", sa.JSON(), nullable=True),
        sa.Column("passthrough_filters", sa.JSON(), nullable=True),
    )

    # Create table element_type_to_property_set
    op.create_table(
        "element_type_to_property_set",
        sa.Column(
            "id",
            UUIDType(binary=False),
            sa.ForeignKey("element_type.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "property_set_id",
            UUIDType(binary=False),
            sa.ForeignKey("property_set.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("order_no", sa.Integer(), nullable=False),
    )


def downgrade():
    op.drop_table("element_type_to_property_set")

    op.drop_table("sink")

    op.drop_table("source")

    op.drop_table("thing_node")

    op.drop_table("property_metadata")

    op.drop_table("property_set")

    op.drop_table("element_type")
