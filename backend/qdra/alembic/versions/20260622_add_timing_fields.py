"""Add input, started_at, finished_at columns to planning_runs table

Revision ID: 20260622_add_timing_fields
Revises: 20260621_add_name_plans
Create Date: 2026-06-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260622_add_timing_fields"
down_revision: Union[str, None] = "20260621_add_name_plans"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("planning_runs", sa.Column("input", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("planning_runs", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("planning_runs", sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("planning_runs", "finished_at")
    op.drop_column("planning_runs", "started_at")
    op.drop_column("planning_runs", "input")
