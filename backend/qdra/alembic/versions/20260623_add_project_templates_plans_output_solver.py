"""add project_templates_plans_output_solver table

Revision ID: 20260623_plan_output_solver
Revises: 20260622_drop_reasoning_jobs
Create Date: 2024-06-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '20260623_plan_output_solver'
down_revision = '20260622_drop_reasoning_jobs'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'project_templates_plans_output_solver',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            'project_template_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('project_templates.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('new_plan_defaults', postgresql.JSONB(), nullable=True),
        sa.Column('results_view_defaults', postgresql.JSONB(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint('project_template_id', name='uq_template_plan_output_solver'),
    )


def downgrade():
    op.drop_table('project_templates_plans_output_solver')
