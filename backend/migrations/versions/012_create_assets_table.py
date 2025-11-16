"""Create assets table

Revision ID: 012
Revises: 011
Create Date: 2025-11-16

This migration creates the assets table for tracking uploaded files in S3,
including brand images, generated videos, and other media assets.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = '012'
down_revision: Union[str, None] = '011'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create assets table with all required columns, constraints, and indexes."""
    op.create_table(
        'assets',
        # Primary key: UUID generated server-side
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),

        # Foreign key to users table
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),

        # S3 storage information
        sa.Column('s3_key', sa.Text, nullable=False, unique=True),
        sa.Column('original_filename', sa.String(255), nullable=False),

        # File metadata
        sa.Column('file_size', sa.BigInteger, nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('asset_type', sa.String(50), nullable=False),

        # Additional metadata as JSONB (flexible schema)
        sa.Column('metadata', JSONB, nullable=True),

        # Timestamps (UTC)
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

        # Foreign key constraint
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Create individual indexes
    op.create_index('idx_assets_user_id', 'assets', ['user_id'])
    op.create_index('idx_assets_s3_key', 'assets', ['s3_key'], unique=True)
    op.create_index('idx_assets_asset_type', 'assets', ['asset_type'])
    op.create_index('idx_assets_created_at', 'assets', ['created_at'])

    # Create composite indexes for common query patterns
    op.create_index('idx_assets_user_created', 'assets', ['user_id', 'created_at'])
    op.create_index('idx_assets_type_created', 'assets', ['asset_type', 'created_at'])


def downgrade() -> None:
    """Drop assets table and all its indexes."""
    # Drop composite indexes
    op.drop_index('idx_assets_type_created', table_name='assets')
    op.drop_index('idx_assets_user_created', table_name='assets')

    # Drop individual indexes
    op.drop_index('idx_assets_created_at', table_name='assets')
    op.drop_index('idx_assets_asset_type', table_name='assets')
    op.drop_index('idx_assets_s3_key', table_name='assets')
    op.drop_index('idx_assets_user_id', table_name='assets')

    # Drop table
    op.drop_table('assets')
