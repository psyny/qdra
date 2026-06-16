"""Add parameter definition metadata fields

Revision ID: 007
Revises: 006
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '007'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE project_template_parameter_definitions
            ADD COLUMN is_label      BOOLEAN NOT NULL DEFAULT false,
            ADD COLUMN is_unique     BOOLEAN NOT NULL DEFAULT false,
            ADD COLUMN is_searchable BOOLEAN NOT NULL DEFAULT false,
            ADD COLUMN is_hidden     BOOLEAN NOT NULL DEFAULT false,
            ADD COLUMN default_value TEXT,
            ADD COLUMN validation    JSONB;
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE project_template_parameter_definitions
            DROP COLUMN IF EXISTS is_label,
            DROP COLUMN IF EXISTS is_unique,
            DROP COLUMN IF EXISTS is_searchable,
            DROP COLUMN IF EXISTS is_hidden,
            DROP COLUMN IF EXISTS default_value,
            DROP COLUMN IF EXISTS validation;
    """)
