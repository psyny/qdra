"""Constraint-based models migration

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop old tables if they exist
    op.drop_table('field_definitions', if_exists=True)
    op.drop_table('object_types', if_exists=True)
    op.drop_table('projects', if_exists=True)
    
    # Create new tables
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    op.create_table(
        'materials',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
    )
    
    op.create_table(
        'parameters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('material_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('domain', sa.String(255), nullable=False),
        sa.Column('key', sa.String(255), nullable=False),
        sa.Column('value_string', sa.String(255), nullable=True),
        sa.Column('value_number', sa.Float(), nullable=True),
        sa.Column('value_boolean', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ),
        sa.CheckConstraint(
            "(value_string IS NOT NULL)::integer + (value_number IS NOT NULL)::integer + (value_boolean IS NOT NULL)::integer = 1",
            name='ck_exactly_one_value'
        ),
    )
    
    op.create_table(
        'recipes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
    )
    
    op.create_table(
        'slots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('recipe_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('kind', sa.String(50), nullable=False),
        sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ),
    )
    
    op.create_table(
        'options',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('slot_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['slot_id'], ['slots.id'], ),
    )
    
    op.create_table(
        'parameter_constraints',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('option_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('domain', sa.String(255), nullable=False),
        sa.Column('key', sa.String(255), nullable=False),
        sa.Column('operator', sa.String(50), nullable=False),
        sa.Column('value_string', sa.String(255), nullable=True),
        sa.Column('value_number', sa.Float(), nullable=True),
        sa.Column('value_boolean', sa.Boolean(), nullable=True),
        sa.Column('is_wildcard', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['option_id'], ['options.id'], ),
    )


def downgrade() -> None:
    op.drop_table('parameter_constraints')
    op.drop_table('options')
    op.drop_table('slots')
    op.drop_table('recipes')
    op.drop_table('parameters')
    op.drop_table('materials')
    op.drop_table('projects')
