"""add can_access to project_user_permissions

Revision ID: 20260624_can_access
Revises: 20260624_access_control
Create Date: 2024-06-24 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260624_can_access'
down_revision = '20260624_access_control'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'project_user_permissions',
        sa.Column('can_access', sa.Boolean(), nullable=False, server_default='false'),
    )


def downgrade():
    op.drop_column('project_user_permissions', 'can_access')
