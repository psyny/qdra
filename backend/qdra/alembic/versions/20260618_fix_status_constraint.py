"""fix status constraint to include ready

Revision ID: 20260618_fix_status
Revises: 20260618_add_image_status
Create Date: 2024-06-18 21:19:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260618_fix_status'
down_revision = '20260618_add_image_status'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the old constraint
    op.execute("ALTER TABLE image_assets DROP CONSTRAINT IF EXISTS check_status_valid")
    
    # Add the new constraint with 'ready' included
    op.execute("ALTER TABLE image_assets ADD CONSTRAINT check_status_valid CHECK (status IN ('pending', 'ready', 'active', 'failed'))")


def downgrade():
    # Drop the new constraint
    op.execute("ALTER TABLE image_assets DROP CONSTRAINT IF EXISTS check_status_valid")
    
    # Add the old constraint without 'ready'
    op.execute("ALTER TABLE image_assets ADD CONSTRAINT check_status_valid CHECK (status IN ('pending', 'active', 'failed'))")
