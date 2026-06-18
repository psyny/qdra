"""drop is_primary column from image_assets

Revision ID: 20260618_drop_is_primary
Revises: 20260618_fix_status
Create Date: 2024-06-18 21:34:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260618_drop_is_primary'
down_revision = '20260618_fix_status'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the is_primary column
    op.drop_column('image_assets', 'is_primary')


def downgrade():
    # Add back the is_primary column
    op.add_column('image_assets', sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'))
