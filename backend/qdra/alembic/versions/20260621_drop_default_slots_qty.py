"""Drop default_slots_qty from project_template_slot_groups

Revision ID: 20260621_drop_default_slots_qty
Revises: 20260621_add_template_slot_defs
Create Date: 2026-06-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260621_drop_default_slots_qty"
down_revision: Union[str, None] = "20260621_add_template_slot_defs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("project_template_slot_groups", "default_slots_qty")


def downgrade() -> None:
    op.add_column(
        "project_template_slot_groups",
        sa.Column("default_slots_qty", sa.Integer(), nullable=False, server_default="0")
    )
