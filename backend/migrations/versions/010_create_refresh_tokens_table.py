"""Create refresh_tokens table

Revision ID: 010
Revises: 009
Create Date: 2025-11-16

This migration creates the refresh_tokens table for JWT refresh token management.
Refresh tokens are stored hashed (not plaintext) for security.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '010'
down_revision: Union[str, None] = '009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create refresh_tokens table with indexes."""
    op.create_table(
        'refresh_tokens',
        # Primary key: UUID generated server-side
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),

        # Foreign key to users table
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),

        # Token hash (stored hashed, not plaintext for security)
        sa.Column('token_hash', sa.String(255), nullable=False),

        # Expiration tracking
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),

        # Revocation tracking (NULL = active, timestamp = revoked)
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),

        # Timestamp
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

        # Foreign key constraint
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Create composite index for token lookups (user_id + token_hash)
    op.create_index('ix_refresh_tokens_user_token', 'refresh_tokens', ['user_id', 'token_hash'])

    # Create index on user_id for cleanup queries
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])

    # Create index on expires_at for cleanup of expired tokens
    op.create_index('ix_refresh_tokens_expires_at', 'refresh_tokens', ['expires_at'])


def downgrade() -> None:
    """Drop refresh_tokens table and its indexes."""
    op.drop_index('ix_refresh_tokens_expires_at', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_user_id', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_user_token', table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
