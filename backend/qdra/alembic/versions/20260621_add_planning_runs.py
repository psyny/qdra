"""Add planning_runs table

Revision ID: 20260621_add_planning_runs
Revises: 20260621_drop_slot_defs
Create Date: 2026-06-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260621_add_planning_runs"
down_revision: Union[str, None] = "20260621_drop_default_slots_qty"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "planning_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            onupdate=sa.func.now(),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("type", sa.String(length=255), nullable=False),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_planning_runs_status", "planning_runs", ["status"])
    op.create_index("idx_planning_runs_type", "planning_runs", ["type"])


def downgrade() -> None:
    op.drop_index("idx_planning_runs_type", table_name="planning_runs")
    op.drop_index("idx_planning_runs_status", table_name="planning_runs")
    op.drop_table("planning_runs")
