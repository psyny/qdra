"""Add recipe slot definitions

Revision ID: 20260618_add_recipe_slot_definitions
Revises: 20260617_1748_2f09fb9ab52f_cleanup_remove_redundant_columns
Create Date: 2026-06-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260618_slot_defs"
down_revision: Union[str, None] = "2f09fb9ab52f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # project_template_slot_groups
    op.create_table(
        "project_template_slot_groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "entity_type_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_template_entity_types.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(50), nullable=False),
        sa.Column("min_slots", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_slots", sa.Integer(), nullable=True),
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
        sa.UniqueConstraint("entity_type_id", "kind", name="uq_slot_group_entity_type_kind"),
        sa.CheckConstraint("min_slots >= 0", name="ck_slot_group_min_slots_non_negative"),
        sa.CheckConstraint(
            "max_slots IS NULL OR max_slots >= min_slots",
            name="ck_slot_group_max_slots_ge_min",
        ),
    )

    # project_template_slot_definitions
    op.create_table(
        "project_template_slot_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "slot_group_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_template_slot_groups.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("slot_key", sa.String(100), nullable=False),
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
    )

    # project_template_slot_constraints
    op.create_table(
        "project_template_slot_constraints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "slot_group_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_template_slot_groups.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "slot_definition_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_template_slot_definitions.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("domain", sa.String(255), nullable=True),
        sa.Column("key", sa.String(255), nullable=True),
        sa.Column("operator", sa.String(10), nullable=True),
        sa.Column("value_string", sa.Text(), nullable=True),
        sa.Column("value_number", postgresql.DOUBLE_PRECISION(), nullable=True),
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
    )


def downgrade() -> None:
    op.drop_table("project_template_slot_constraints")
    op.drop_table("project_template_slot_definitions")
    op.drop_table("project_template_slot_groups")
