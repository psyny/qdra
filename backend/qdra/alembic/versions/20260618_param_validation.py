"""Simplify parameter validation

Revision ID: 20260618_param_val
Revises: 20260618_slot_defs
Create Date: 2026-06-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260618_param_val"
down_revision: Union[str, None] = "20260618_slot_defs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new validation columns
    op.add_column(
        'project_template_parameter_definitions',
        sa.Column('validation_min', postgresql.DOUBLE_PRECISION(), nullable=True)
    )
    op.add_column(
        'project_template_parameter_definitions',
        sa.Column('validation_max', postgresql.DOUBLE_PRECISION(), nullable=True)
    )
    op.add_column(
        'project_template_parameter_definitions',
        sa.Column('validation_regex', sa.String(), nullable=True)
    )
    
    # Drop the old validation JSONB column
    op.drop_column('project_template_parameter_definitions', 'validation')


def downgrade() -> None:
    # Add back the old validation JSONB column
    op.add_column(
        'project_template_parameter_definitions',
        sa.Column('validation', postgresql.JSONB(), nullable=True)
    )
    
    # Drop the new validation columns
    op.drop_column('project_template_parameter_definitions', 'validation_regex')
    op.drop_column('project_template_parameter_definitions', 'validation_max')
    op.drop_column('project_template_parameter_definitions', 'validation_min')
