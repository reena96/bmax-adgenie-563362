"""Create password_reset_tokens table

Revision ID: 011
Revises: 010
Create Date: 2025-11-16

This migration creates the password_reset_tokens table for password reset flow.
Tokens are single-use with 1-hour expiration.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '011'
down_revision: Union[str, None] = '010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create password_reset_tokens table with indexes."""
    op.create_table(
        'password_reset_tokens',
        # Primary key: UUID generated server-side
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),

        # Foreign key to users table
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),

        # Token hash (6-digit code hashed for security)
        sa.Column('token_hash', sa.String(255), nullable=False),

        # Expiration tracking (1-hour expiry)
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),

        # Single-use tracking (NULL = unused, timestamp = used)
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),

        # Timestamp
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

        # Foreign key constraint
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Create index on user_id for user lookup
    op.create_index('ix_password_reset_tokens_user_id', 'password_reset_tokens', ['user_id'])

    # Create index on expires_at for cleanup of expired tokens
    op.create_index('ix_password_reset_tokens_expires_at', 'password_reset_tokens', ['expires_at'])

    # Create composite index for token validation (user_id + token_hash)
    op.create_index('ix_password_reset_tokens_user_token', 'password_reset_tokens', ['user_id', 'token_hash'])


def downgrade() -> None:
    """Drop password_reset_tokens table and its indexes."""
    op.drop_index('ix_password_reset_tokens_user_token', table_name='password_reset_tokens')
    op.drop_index('ix_password_reset_tokens_expires_at', table_name='password_reset_tokens')
    op.drop_index('ix_password_reset_tokens_user_id', table_name='password_reset_tokens')
    op.drop_table('password_reset_tokens')
