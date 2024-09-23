"""create_tables_for_virtual_structure

Revision ID: 5cfafc3cf470
Revises: aaf97187894d
Create Date: 2024-07-04 11:54:37.172484

"""

import sqlalchemy as sa
from sqlalchemy_utils import UUIDType

from alembic import op

# revision identifiers, used by Alembic.
revision = "5cfafc3cf470"
down_revision = "aaf97187894d"
branch_labels = None
depends_on = None


def upgrade():
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
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("stakeholder_key", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.Column("reference_table_name", sa.String(length=100), unique=True, nullable=False),
        sa.Column("property_set_type", sa.String(length=50), nullable=False),
        sa.UniqueConstraint("name", name="_property_set_name_uc"),
        sa.UniqueConstraint(
            "external_id",
            "stakeholder_key",
            name="_property_set_external_id_stakeholder_key_uc",
        ),
    )

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
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("stakeholder_key", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.UniqueConstraint("name", name="_element_type_name_uc"),
        sa.UniqueConstraint(
            "external_id",
            "stakeholder_key",
            name="_element_type_external_id_stakeholder_key_uc",
        ),
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
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("stakeholder_key", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.Column("parent_external_node_id", sa.String(length=255), nullable=True),
        sa.Column("element_type_external_id", sa.String(length=255), nullable=False),
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
        sa.Column("meta_data", sa.JSON(), nullable=True),
        sa.UniqueConstraint("name", name="_thing_node_name_uc"),
        sa.UniqueConstraint(
            "external_id",
            "stakeholder_key",
            name="_thing_node_external_id_stakeholder_key_uc",
        ),
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
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("stakeholder_key", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=255), nullable=False),
        sa.Column("visible", sa.Boolean(), default=True),
        sa.Column("display_path", sa.String(length=255), nullable=False),
        sa.Column("adapter_key", sa.String(length=255), nullable=False),
        sa.Column("source_id", sa.String(length=255), nullable=False),
        sa.Column("ref_key", sa.String(length=255), nullable=True),
        sa.Column("ref_id", sa.String(length=255), nullable=False),
        sa.Column("meta_data", sa.JSON(), nullable=True),
        sa.Column("preset_filters", sa.JSON(), nullable=False),
        sa.Column("passthrough_filters", sa.JSON(), nullable=True),
        sa.Column("thing_node_external_ids", sa.JSON(), nullable=True),
        sa.UniqueConstraint(
            "external_id",
            "stakeholder_key",
            name="_source_external_id_stakeholder_key_uc",
        ),
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
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("stakeholder_key", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=255), nullable=False),
        sa.Column("visible", sa.Boolean(), default=True),
        sa.Column("display_path", sa.String(length=255), nullable=False),
        sa.Column("adapter_key", sa.String(length=255), nullable=False),
        sa.Column("sink_id", sa.String(length=255), nullable=False),
        sa.Column("ref_key", sa.String(length=255), nullable=True),
        sa.Column("ref_id", sa.String(length=255), nullable=False),
        sa.Column("meta_data", sa.JSON(), nullable=True),
        sa.Column("preset_filters", sa.JSON(), nullable=False),
        sa.Column("passthrough_filters", sa.JSON(), nullable=True),
        sa.Column("thing_node_external_ids", sa.JSON(), nullable=True),
        sa.UniqueConstraint(
            "external_id",
            "stakeholder_key",
            name="_sink_external_id_stakeholder_key_uc",
        ),
    )

    op.create_table(
        "thingnode_source_association",
        sa.Column(
            "thing_node_id",
            UUIDType(binary=False),
            sa.ForeignKey("thing_node.id"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "source_id",
            UUIDType(binary=False),
            sa.ForeignKey("source.id"),
            primary_key=True,
            nullable=False,
        ),
    )

    op.create_table(
        "thingnode_sink_association",
        sa.Column(
            "thing_node_id",
            UUIDType(binary=False),
            sa.ForeignKey("thing_node.id"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "sink_id",
            UUIDType(binary=False),
            sa.ForeignKey("sink.id"),
            primary_key=True,
            nullable=False,
        ),
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
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("stakeholder_key", sa.String(length=255), nullable=False),
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
        sa.UniqueConstraint(
            "external_id",
            "stakeholder_key",
            name="_property_metadata_external_id_stakeholder_key_uc",
        ),
    )

    # Create table element_type_to_property_set
    op.create_table(
        "element_type_to_property_set",
        sa.Column(
            "element_type_id",
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
    op.drop_table("thingnode_source_association")

    op.drop_table("thingnode_sink_association")

    op.drop_table("element_type_to_property_set")

    op.drop_table("sink")

    op.drop_table("source")

    op.drop_table("thing_node")

    op.drop_table("property_metadata")

    op.drop_table("property_set")

    op.drop_table("element_type")
