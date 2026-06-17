"""cleanup_remove_redundant_columns

Revision ID: 2f09fb9ab52f
Revises: 001_entity_abstraction
Create Date: 2026-06-17 17:48:26.279448

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f09fb9ab52f'
down_revision: Union[str, None] = '001_entity_abstraction'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop entities.kind column (now derived from entity_type_id)
    op.drop_index('ix_entities_kind', table_name='entities')
    op.drop_column('entities', 'kind')
    
    # Drop image_assets.project_id column (now derived from entity_id -> entity.project_id)
    op.drop_column('image_assets', 'project_id')


def downgrade() -> None:
    # Re-add image_assets.project_id column
    op.add_column('image_assets', sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=False))
    
    # Re-add entities.kind column
    op.add_column('entities', sa.Column('kind', sa.String(50), nullable=False))
    op.create_index('ix_entities_kind', 'entities', ['kind'])
