"""add status to image_assets

Revision ID: 20260618_add_image_status
Revises: 20260618_add_image_size_px
Create Date: 2024-06-18 18:01:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260618_add_image_status'
down_revision = '20260618_add_image_size_px'
branch_labels = None
depends_on = None


def upgrade():
    # Add status column to image_assets table
    op.add_column('image_assets', sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'))
    
    # Add check constraint for status values
    op.execute("ALTER TABLE image_assets ADD CONSTRAINT check_status_valid CHECK (status IN ('pending', 'ready', 'active', 'failed'))")


def downgrade():
    # Remove check constraint
    op.execute("ALTER TABLE image_assets DROP CONSTRAINT check_status_valid")
    
    # Remove status column
    op.drop_column('image_assets', 'status')
