"""Redesign slot definitions with default_slots_qty and slot_idx

Revision ID: 20260621_redesign_slot_definitions
Revises: 20260620_add_entity_group
Create Date: 2026-06-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260621_slot_def_redesign"
down_revision: Union[str, None] = "20260620_add_entity_group"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename 'kind' to 'type' in project_template_slot_groups
    op.alter_column(
        'project_template_slot_groups',
        'kind',
        new_column_name='type',
        existing_type=sa.String(50)
    )
    
    # Add default_slots_qty to project_template_slot_groups
    op.add_column(
        'project_template_slot_groups',
        sa.Column('default_slots_qty', sa.Integer(), nullable=False, server_default='0')
    )
    
    # Add slot_idx to project_template_slot_definitions
    op.add_column(
        'project_template_slot_definitions',
        sa.Column('slot_idx', sa.Integer(), nullable=True)
    )


def downgrade() -> None:
    # Remove slot_idx from project_template_slot_definitions
    op.drop_column('project_template_slot_definitions', 'slot_idx')
    
    # Remove default_slots_qty from project_template_slot_groups
    op.drop_column('project_template_slot_groups', 'default_slots_qty')
    
    # Rename 'type' back to 'kind' in project_template_slot_groups
    op.alter_column(
        'project_template_slot_groups',
        'type',
        new_column_name='kind',
        existing_type=sa.String(50)
    )
