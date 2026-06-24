"""add access control tables (users, user_app_permissions, project_user_permissions)

Revision ID: 20260624_access_control
Revises: 20260623_plan_output_solver
Create Date: 2024-06-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '20260624_access_control'
down_revision = '20260623_plan_output_solver'
branch_labels = None
depends_on = None


def upgrade():
    # users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('login_name', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('display_name', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('login_name', name='uq_users_login_name'),
    )
    op.create_index('ix_users_login_name', 'users', ['login_name'])
    op.create_index('ix_users_is_active', 'users', ['is_active'])

    # user_app_permissions table
    op.create_table(
        'user_app_permissions',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('can_manage_users', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_create_projects', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_edit_projects', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_delete_projects', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_create_templates', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_edit_templates', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_delete_templates', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # project_user_permissions table
    op.create_table(
        'project_user_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('can_manage_project_users', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_create_material', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_edit_material', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_delete_material', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_create_recipe', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_edit_recipe', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_delete_recipe', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_run_plan', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'project_id', name='uq_project_user_permissions_user_project'),
    )
    op.create_index('ix_project_user_permissions_project_id', 'project_user_permissions', ['project_id'])
    op.create_index('ix_project_user_permissions_user_id', 'project_user_permissions', ['user_id'])


def downgrade():
    op.drop_index('ix_project_user_permissions_user_id', table_name='project_user_permissions')
    op.drop_index('ix_project_user_permissions_project_id', table_name='project_user_permissions')
    op.drop_table('project_user_permissions')
    op.drop_table('user_app_permissions')
    op.drop_index('ix_users_is_active', table_name='users')
    op.drop_index('ix_users_login_name', table_name='users')
    op.drop_table('users')
