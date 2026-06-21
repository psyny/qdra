"""Drop slot definitions and constraints tables

Revision ID: 20260621_drop_slot_defs
Revises: 20260618_slot_defs
Create Date: 2026-06-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260621_drop_slot_defs"
down_revision: Union[str, None] = "20260620_add_entity_group"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop tables in reverse order of creation (due to foreign keys)
    op.drop_table("project_template_slot_constraints")
    op.drop_table("project_template_slot_definitions")


def downgrade() -> None:
    # Recreate tables (for rollback)
    # project_template_slot_definitions
    op.create_table(
        "project_template_slot_definitions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "slot_group_id",
            sa.UUID(),
            sa.ForeignKey("project_template_slot_groups.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("slot_key", sa.String(length=100), nullable=False),
        sa.Column("slot_idx", sa.Integer(), nullable=True),
        sa.Column("min_occurrences", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_occurrences", sa.Integer(), nullable=True),
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
            nullable=False,
        ),
        sa.UniqueConstraint("slot_group_id", "slot_key", name="uq_slot_def_group_key"),
        sa.CheckConstraint("min_occurrences >= 0", name="ck_slot_def_min_occurrences_non_negative"),
        sa.CheckConstraint(
            "max_occurrences IS NULL OR max_occurrences >= min_occurrences",
            name="ck_slot_def_max_occurrences_ge_min",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # project_template_slot_constraints
    op.create_table(
        "project_template_slot_constraints",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "slot_group_id",
            sa.UUID(),
            sa.ForeignKey("project_template_slot_groups.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "slot_definition_id",
            sa.UUID(),
            sa.ForeignKey("project_template_slot_definitions.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("domain", sa.String(length=255), nullable=True),
        sa.Column("key", sa.String(length=255), nullable=True),
        sa.Column("operator", sa.String(length=10), nullable=True),
        sa.Column("value_string", sa.Text(), nullable=True),
        sa.Column("value_number", sa.Float(), nullable=True),
        sa.Column("value_boolean", sa.Boolean(), nullable=True),
        sa.Column("is_wildcard", sa.Boolean(), nullable=False, server_default="false"),
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
            nullable=False,
        ),
        sa.CheckConstraint(
            "(slot_group_id IS NOT NULL AND slot_definition_id IS NULL) OR "
            "(slot_group_id IS NULL AND slot_definition_id IS NOT NULL)",
            name="ck_slot_constraint_exactly_one_parent",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
