"""Add image_assets table

Revision ID: 005
Revises: 004
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if table already exists (from partial migration)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'image_assets' in inspector.get_table_names():
        # Table already exists, skip migration
        return
    
    # Create ENUM types using raw SQL with IF NOT EXISTS
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE image_owner_type AS ENUM ('material', 'recipe');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE storage_backend AS ENUM ('local', 's3');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Use raw SQL to create table to avoid SQLAlchemy trying to create ENUM types
    op.execute("""
        CREATE TABLE image_assets (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id UUID NOT NULL REFERENCES projects(id),
            owner_type image_owner_type NOT NULL,
            owner_id UUID NOT NULL,
            storage_backend storage_backend NOT NULL,
            storage_key TEXT NOT NULL,
            original_filename TEXT,
            mime_type TEXT NOT NULL,
            file_size_bytes BIGINT,
            width INTEGER,
            height INTEGER,
            alt_text TEXT,
            is_primary BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            CONSTRAINT check_owner_type CHECK (owner_type IN ('material', 'recipe')),
            CONSTRAINT check_storage_backend CHECK (storage_backend IN ('local', 's3'))
        );
    """)


def downgrade() -> None:
    op.drop_table('image_assets')
    postgresql.ENUM(name='image_owner_type').drop(op.get_bind())
    postgresql.ENUM(name='storage_backend').drop(op.get_bind())
