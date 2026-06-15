"""Add project templates and related tables

Revision ID: 006
Revises: 005
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create project_templates table first
    op.execute("""
        CREATE TABLE project_templates (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name TEXT NOT NULL,
            description TEXT,
            version INTEGER NOT NULL DEFAULT 1,
            is_builtin BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        );
    """)

    # Create project_template_material_types table
    op.execute("""
        CREATE TABLE project_template_material_types (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_template_id UUID NOT NULL REFERENCES project_templates(id),
            name TEXT NOT NULL,
            description TEXT,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        );
    """)

    # Create project_template_recipe_types table
    op.execute("""
        CREATE TABLE project_template_recipe_types (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_template_id UUID NOT NULL REFERENCES project_templates(id),
            name TEXT NOT NULL,
            description TEXT,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        );
    """)

    # Create project_template_parameter_definitions table
    op.execute("""
        CREATE TABLE project_template_parameter_definitions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_template_id UUID NOT NULL REFERENCES project_templates(id),
            owner_kind TEXT NOT NULL,
            owner_type_id UUID NOT NULL,
            domain TEXT NOT NULL,
            key TEXT NOT NULL,
            value_type TEXT NOT NULL,
            label TEXT,
            description TEXT,
            required BOOLEAN NOT NULL DEFAULT false,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        );
    """)

    # Add project_template_id to projects table
    op.add_column('projects', sa.Column('project_template_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_projects_project_template_id', 'projects', 'project_templates', ['project_template_id'], ['id'])


def downgrade() -> None:
    # Drop tables in reverse order of creation
    op.drop_table('project_template_parameter_definitions')
    op.drop_table('project_template_recipe_types')
    op.drop_table('project_template_material_types')
    op.drop_table('project_templates')
    
    # Drop column from projects
    op.drop_constraint('fk_projects_project_template_id', 'projects', type_='foreignkey')
    op.drop_column('projects', 'project_template_id')
