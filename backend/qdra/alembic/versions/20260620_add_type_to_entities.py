"""add group field to entities

Revision ID: 20260620_add_entity_group
Revises: 20260618_drop_is_primary
Create Date: 2026-06-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260620_add_entity_group"
down_revision: Union[str, None] = "20260620_add_entity_type"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add group column to entities table
    op.add_column('entities', sa.Column('group', sa.String(length=255), nullable=False, server_default=''))


def downgrade() -> None:
    # Remove group column
    op.drop_column('entities', 'group')
