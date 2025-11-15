"""Add authentication fields and password reset

Revision ID: 002
Revises: 001
Create Date: 2025-11-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add google_sub column to users table
    op.add_column('users', sa.Column('google_sub', sa.String(255), nullable=True))
    op.create_index('ix_users_google_sub', 'users', ['google_sub'], unique=True)

    # Make password_hash nullable for OAuth-only users
    op.alter_column('users', 'password_hash', nullable=True)

    # Rename token column to token_hash in sessions table
    op.alter_column('sessions', 'token', new_column_name='token_hash')

    # Create password_resets table
    op.create_table(
        'password_resets',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token', sa.String(255), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('ix_password_resets_user_id', 'password_resets', ['user_id'])
    op.create_index('ix_password_resets_token', 'password_resets', ['token'], unique=True)
    op.create_index('ix_password_resets_expires_at', 'password_resets', ['expires_at'])


def downgrade() -> None:
    # Drop password_resets table
    op.drop_table('password_resets')

    # Rename token_hash back to token in sessions table
    op.alter_column('sessions', 'token_hash', new_column_name='token')

    # Make password_hash non-nullable again
    op.alter_column('users', 'password_hash', nullable=False)

    # Remove google_sub column from users table
    op.drop_index('ix_users_google_sub', 'users')
    op.drop_column('users', 'google_sub')
