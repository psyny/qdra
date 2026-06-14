"""Add recipe parameters table

Revision ID: 003
Revises: 002
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'recipe_parameters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('recipe_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('domain', sa.String(255), nullable=False),
        sa.Column('key', sa.String(255), nullable=False),
        sa.Column('value_string', sa.String(255), nullable=True),
        sa.Column('value_number', sa.Float(), nullable=True),
        sa.Column('value_boolean', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ),
        sa.CheckConstraint(
            "(value_string IS NOT NULL)::integer + (value_number IS NOT NULL)::integer + (value_boolean IS NOT NULL)::integer = 1",
            name='ck_recipe_exactly_one_value'
        ),
    )


def downgrade() -> None:
    op.drop_table('recipe_parameters')
