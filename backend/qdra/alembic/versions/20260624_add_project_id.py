"""add project_id to planning_runs

Revision ID: 20260624_add_project_id_to_planning_runs
Revises: 20260624_access_control
Create Date: 2024-06-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '20260624_add_project_id'
down_revision = '20260624_can_access'
branch_labels = None
depends_on = None


def upgrade():
    # Add project_id column as nullable first to handle existing data
    op.add_column(
        'planning_runs',
        sa.Column(
            'project_id',
            postgresql.UUID(as_uuid=True),
            nullable=True
        )
    )
    
    # Delete existing planning_runs that don't have a project_id
    # These are invalid in the new system since they can't be associated with a project
    op.execute("DELETE FROM planning_runs WHERE project_id IS NULL")
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_planning_runs_project_id',
        'planning_runs',
        'projects',
        ['project_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    # Add index
    op.create_index('idx_planning_runs_project_id', 'planning_runs', ['project_id'])
    
    # Make the column NOT NULL after deleting invalid rows
    op.alter_column(
        'planning_runs',
        'project_id',
        nullable=False
    )


def downgrade():
    op.drop_index('idx_planning_runs_project_id', table_name='planning_runs')
    op.drop_constraint('fk_planning_runs_project_id', 'planning_runs', type_='foreignkey')
    op.drop_column('planning_runs', 'project_id')
