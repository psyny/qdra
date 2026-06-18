"""Template Views Editor

Revision ID: 20260618_views_editor
Revises: 20260618_param_val
Create Date: 2026-06-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260618_views_editor"
down_revision: Union[str, None] = "20260618_param_val"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === project_template_views changes ===
    
    # Add new columns
    op.add_column(
        'project_template_views',
        sa.Column('view_key', sa.String(255), nullable=True)
    )
    op.add_column(
        'project_template_views',
        sa.Column('label', sa.String(255), nullable=True)
    )
    op.add_column(
        'project_template_views',
        sa.Column('description', sa.String(1000), nullable=True)
    )
    op.add_column(
        'project_template_views',
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false')
    )
    
    # Migrate data from view_name to view_key
    op.execute("""
        UPDATE project_template_views 
        SET view_key = view_name
    """)
    
    # Make view_key not nullable after migration
    op.alter_column(
        'project_template_views',
        'view_key',
        nullable=False
    )
    
    # Drop the old view_name column
    op.drop_column('project_template_views', 'view_name')
    
    # === project_template_view_configs changes ===
    
    # Rename slots to display_slots
    op.alter_column(
        'project_template_view_configs',
        'slots',
        new_column_name='display_slots'
    )
    
    # Drop entity_kind column
    op.drop_column('project_template_view_configs', 'entity_kind')


def downgrade() -> None:
    # === project_template_view_configs downgrade ===
    
    # Add back entity_kind column
    op.add_column(
        'project_template_view_configs',
        sa.Column('entity_kind', sa.String(50), nullable=True)
    )
    
    # Rename display_slots back to slots
    op.alter_column(
        'project_template_view_configs',
        'display_slots',
        new_column_name='slots'
    )
    
    # === project_template_views downgrade ===
    
    # Add back view_name column
    op.add_column(
        'project_template_views',
        sa.Column('view_name', sa.String(255), nullable=True)
    )
    
    # Migrate data from view_key to view_name
    op.execute("""
        UPDATE project_template_views 
        SET view_name = view_key
    """)
    
    # Make view_name not nullable after migration
    op.alter_column(
        'project_template_views',
        'view_name',
        nullable=False
    )
    
    # Drop the new columns
    op.drop_column('project_template_views', 'is_system')
    op.drop_column('project_template_views', 'description')
    op.drop_column('project_template_views', 'label')
    op.drop_column('project_template_views', 'view_key')
