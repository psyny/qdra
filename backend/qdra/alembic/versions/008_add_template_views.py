"""Add template views and view configs

Revision ID: 008
Revises: 007
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '008'
down_revision: Union[str, None] = '007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE project_template_views (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_template_id UUID NOT NULL REFERENCES project_templates(id),
            view_name TEXT NOT NULL,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        );
    """)

    op.execute("""
        CREATE TABLE project_template_view_configs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            view_id UUID NOT NULL REFERENCES project_template_views(id) ON DELETE CASCADE,
            entity_type TEXT NOT NULL,
            filter_params JSONB,
            slots JSONB NOT NULL DEFAULT '[]'::jsonb,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        );
    """)


def downgrade() -> None:
    op.drop_table('project_template_view_configs')
    op.drop_table('project_template_views')
