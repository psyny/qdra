"""add view unique constraint

Revision ID: 20260618_view_unique
Revises: 20260618_views_editor
Create Date: 2026-06-18 15:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260618_view_unique'
down_revision = '20260618_views_editor'
branch_labels = None
depends_on = None


def upgrade():
    # First, remove any duplicate views that may exist
    # This is a data cleanup step to handle the race condition issue
    op.execute("""
        DELETE FROM project_template_views ptv1
        WHERE id IN (
            SELECT ptv2.id
            FROM project_template_views ptv2
            WHERE ptv2.project_template_id = ptv1.project_template_id
            AND ptv2.view_key = ptv1.view_key
            AND ptv2.id > ptv1.id
        )
    """)
    
    # Then add the unique constraint
    op.create_unique_constraint(
        'uq_view_template_key',
        'project_template_views',
        ['project_template_id', 'view_key']
    )


def downgrade():
    op.drop_constraint(
        'uq_view_template_key',
        'project_template_views',
        type_='unique'
    )
