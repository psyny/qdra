"""bridge migration for renamed group field

Revision ID: 20260620_add_entity_type
Revises: 20260618_drop_is_primary
Create Date: 2026-06-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260620_add_entity_type"
down_revision: Union[str, None] = "20260618_drop_is_primary"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the old 'type' column if it exists from the previous migration
    # This is a bridge migration to handle the rename from 'type' to 'group'
    # Check if column exists first to avoid transaction errors
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('entities')]
    if 'type' in columns:
        op.drop_column('entities', 'type')


def downgrade() -> None:
    # This is a no-op since we're moving to the new 'group' migration
    pass
