"""Create brands table

Revision ID: 003
Revises: 002
Create Date: 2025-11-15

This migration creates the brands table with JSONB columns for product images
and brand guidelines, and establishes foreign key relationship to users.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create brands table with JSONB columns and foreign key to users."""
    op.create_table(
        'brands',
        # Primary key: UUID generated server-side
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),

        # Foreign key to users table (CASCADE on delete - delete brands when user is deleted)
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),

        # Brand information
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),

        # JSONB columns for flexible data storage
        # product_images: Array of S3 URLs - e.g., ["s3://bucket/image1.png", "s3://bucket/image2.png"]
        sa.Column('product_images', JSONB, nullable=False, server_default='[]'),

        # brand_guidelines: Object with colors, fonts, tone, assets
        # e.g., {"colors": ["#FFEB3B"], "fonts": ["Arial"], "tone": "professional"}
        sa.Column('brand_guidelines', JSONB, nullable=False, server_default='{}'),

        # Timestamps (UTC)
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

        # Foreign key constraint
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Composite index for listing user's brands ordered by creation date
    op.create_index('ix_brands_user_id_created_at', 'brands', ['user_id', 'created_at'])

    # Single index on user_id for foreign key lookups
    op.create_index('ix_brands_user_id', 'brands', ['user_id'])


def downgrade() -> None:
    """Drop brands table and its indexes."""
    op.drop_index('ix_brands_user_id', table_name='brands')
    op.drop_index('ix_brands_user_id_created_at', table_name='brands')
    op.drop_table('brands')
