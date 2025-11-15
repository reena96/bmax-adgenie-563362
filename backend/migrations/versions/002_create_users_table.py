"""Create users table

Revision ID: 002
Revises: 001
Create Date: 2025-11-15

This migration creates the users table with UUID primary key, email authentication,
subscription types, and soft-delete support.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create users table with all required columns and constraints."""
    op.create_table(
        'users',
        # Primary key: UUID generated server-side
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),

        # Authentication and profile fields
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),

        # Subscription type (enum)
        sa.Column('subscription_type', sa.Enum('free', 'pro', 'enterprise', name='subscription_type'),
                  nullable=False, server_default='free'),

        # Timestamps (UTC)
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

        # Soft delete support
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Create index on email for authentication lookups
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # Create index on deleted_at for filtering active users
    op.create_index('ix_users_deleted_at', 'users', ['deleted_at'])


def downgrade() -> None:
    """Drop users table and its indexes."""
    op.drop_index('ix_users_deleted_at', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
