"""add image_size_px to projects

Revision ID: 20260618_add_image_size_px
Revises: 20260618_view_unique
Create Date: 2024-06-18 17:57:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260618_add_image_size_px'
down_revision = '20260618_view_unique'
branch_labels = None
depends_on = None


def upgrade():
    # Add image_size_px column to projects table
    op.add_column('projects', sa.Column('image_size_px', sa.Integer(), nullable=False, server_default='256'))
    
    # Add check constraints for image_size_px range
    op.execute("ALTER TABLE projects ADD CONSTRAINT check_image_size_min CHECK (image_size_px >= 32)")
    op.execute("ALTER TABLE projects ADD CONSTRAINT check_image_size_max CHECK (image_size_px <= 1024)")


def downgrade():
    # Remove check constraints
    op.execute("ALTER TABLE projects DROP CONSTRAINT check_image_size_max")
    op.execute("ALTER TABLE projects DROP CONSTRAINT check_image_size_min")
    
    # Remove image_size_px column
    op.drop_column('projects', 'image_size_px')
