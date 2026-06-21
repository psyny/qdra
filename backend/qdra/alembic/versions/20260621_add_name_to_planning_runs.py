"""Add name column to planning_runs table

Revision ID: 20260621_add_name_to_planning_runs
Revises: 20260621_add_planning_runs
Create Date: 2026-06-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260621_add_name_plans"
down_revision: Union[str, None] = "20260621_add_planning_runs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("planning_runs", sa.Column("name", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("planning_runs", "name")
