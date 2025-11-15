"""Create ad_projects table

Revision ID: 004
Revises: 003
Create Date: 2025-11-15

This migration creates the ad_projects table with status tracking, conversation history,
and ad details stored as JSONB. Establishes foreign keys to users and brands.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create ad_projects table with status enum and JSONB columns."""
    op.create_table(
        'ad_projects',
        # Primary key: UUID generated server-side
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),

        # Foreign keys
        sa.Column('brand_id', UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),

        # Project status enum (lifecycle: initial → chat_in_progress → script_generated → etc.)
        sa.Column('status',
                  sa.Enum('initial', 'chat_in_progress', 'script_generated', 'script_approved',
                          'video_generating', 'completed', 'failed', name='ad_project_status'),
                  nullable=False, server_default='initial'),

        # JSONB columns for flexible data storage
        # conversation_history: Array of message objects
        # e.g., [{"id": "uuid", "role": "user", "content": "...", "timestamp": "..."}]
        sa.Column('conversation_history', JSONB, nullable=False, server_default='[]'),

        # ad_details: Object with campaign details
        # e.g., {"targetAudience": "...", "adPlatform": "instagram", "adDuration": 30, "callToAction": "...", "keyMessage": "..."}
        sa.Column('ad_details', JSONB, nullable=False, server_default='{}'),

        # Timestamps (UTC)
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

        # Foreign key constraints
        sa.ForeignKeyConstraint(['brand_id'], ['brands.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='RESTRICT'),
    )

    # Composite index for filtering brand's projects by status
    op.create_index('ix_ad_projects_brand_id_status', 'ad_projects', ['brand_id', 'status'])

    # Composite index for listing user's projects by creation date
    op.create_index('ix_ad_projects_user_id_created_at', 'ad_projects', ['user_id', 'created_at'])

    # Single indexes on foreign keys
    op.create_index('ix_ad_projects_brand_id', 'ad_projects', ['brand_id'])
    op.create_index('ix_ad_projects_user_id', 'ad_projects', ['user_id'])

    # Index on status for filtering across all projects
    op.create_index('ix_ad_projects_status', 'ad_projects', ['status'])


def downgrade() -> None:
    """Drop ad_projects table and its indexes."""
    op.drop_index('ix_ad_projects_status', table_name='ad_projects')
    op.drop_index('ix_ad_projects_user_id', table_name='ad_projects')
    op.drop_index('ix_ad_projects_brand_id', table_name='ad_projects')
    op.drop_index('ix_ad_projects_user_id_created_at', table_name='ad_projects')
    op.drop_index('ix_ad_projects_brand_id_status', table_name='ad_projects')
    op.drop_table('ad_projects')
