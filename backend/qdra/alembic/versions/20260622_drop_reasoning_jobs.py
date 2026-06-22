"""drop reasoning_jobs table

Revision ID: 20260622_drop_reasoning_jobs
Revises: 20260622_add_error_field
Create Date: 2024-06-22 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260622_drop_reasoning_jobs'
down_revision = '20260622_add_error_field'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the reasoning_jobs table if it exists
    # Check if table exists first to avoid errors if it was never created
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'reasoning_jobs' in inspector.get_table_names():
        op.drop_table('reasoning_jobs')


def downgrade():
    # Recreate the reasoning_jobs table (for rollback)
    op.create_table(
        'reasoning_jobs',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', sa.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, default='queued'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('result', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Index('idx_reasoning_jobs_project_id', 'project_id'),
        sa.Index('idx_reasoning_jobs_status', 'status'),
    )
