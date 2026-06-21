"""Add template slot definitions (default and per-slot)

Revision ID: 20260621_add_template_slot_defs
Revises: 20260621_drop_slot_defs
Create Date: 2026-06-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260621_add_template_slot_defs"
down_revision: Union[str, None] = "20260621_drop_slot_defs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create project_template_default_slots
    op.create_table(
        "project_template_default_slots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "slot_group_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_template_slot_groups.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(length=50), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create project_template_default_options
    op.create_table(
        "project_template_default_options",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "default_slot_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_template_default_slots.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("quantity", sa.Float(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create project_template_default_parameter_constraints
    op.create_table(
        "project_template_default_parameter_constraints",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "default_option_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_template_default_options.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("operator", sa.String(length=50), nullable=False),
        sa.Column("value_string", sa.String(length=255), nullable=True),
        sa.Column("value_number", sa.Float(), nullable=True),
        sa.Column("value_boolean", sa.Boolean(), nullable=True),
        sa.Column("is_wildcard", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create project_template_per_slots
    op.create_table(
        "project_template_per_slots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "slot_group_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_template_slot_groups.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(length=50), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create project_template_per_options
    op.create_table(
        "project_template_per_options",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "per_slot_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_template_per_slots.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("quantity", sa.Float(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create project_template_per_parameter_constraints
    op.create_table(
        "project_template_per_parameter_constraints",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "per_option_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_template_per_options.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("operator", sa.String(length=50), nullable=False),
        sa.Column("value_string", sa.String(length=255), nullable=True),
        sa.Column("value_number", sa.Float(), nullable=True),
        sa.Column("value_boolean", sa.Boolean(), nullable=True),
        sa.Column("is_wildcard", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    # Drop tables in reverse order of creation (due to foreign keys)
    op.drop_table("project_template_per_parameter_constraints")
    op.drop_table("project_template_per_options")
    op.drop_table("project_template_per_slots")
    op.drop_table("project_template_default_parameter_constraints")
    op.drop_table("project_template_default_options")
    op.drop_table("project_template_default_slots")
