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
    # Create table element_type
    op.create_table(
        "structure_element_type",
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
        "structure_thing_node",
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
            sa.ForeignKey("structure_thing_node.id"),
            nullable=True,
        ),
        sa.Column(
            "element_type_id",
            UUIDType(binary=False),
            sa.ForeignKey("structure_element_type.id"),
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
        "structure_source",
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
        "structure_sink",
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

    # Create thingnode_source_association table
    op.create_table(
        "structure_thingnode_source_association",
        sa.Column(
            "thingnode_id",
            UUIDType(binary=False),
            sa.ForeignKey("structure_thing_node.id"),
            primary_key=True,
        ),
        sa.Column(
            "source_id",
            UUIDType(binary=False),
            sa.ForeignKey("structure_source.id"),
            primary_key=True,
        ),
    )

    # Create thingnode_sink_association table
    op.create_table(
        "structure_thingnode_sink_association",
        sa.Column(
            "thingnode_id",
            UUIDType(binary=False),
            sa.ForeignKey("structure_thing_node.id"),
            primary_key=True,
        ),
        sa.Column(
            "sink_id", UUIDType(binary=False), sa.ForeignKey("structure_sink.id"), primary_key=True
        ),
    )


def downgrade():
    op.drop_table("structure_thingnode_source_association")

    op.drop_table("structure_thingnode_sink_association")

    op.drop_table("structure_sink")

    op.drop_table("structure_source")

    op.drop_table("structure_thing_node")

    op.drop_table("structure_element_type")
