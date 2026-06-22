"""Add error column to planning_runs table

Revision ID: 20260622_add_error_field
Revises: 20260622_add_timing_fields
Create Date: 2026-06-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260622_add_error_field"
down_revision: Union[str, None] = "20260622_add_timing_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("planning_runs", sa.Column("error", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("planning_runs", "error")
