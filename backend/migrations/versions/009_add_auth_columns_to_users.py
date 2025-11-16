"""Add authentication columns to users table

Revision ID: 009
Revises: 008
Create Date: 2025-11-16

This migration adds authentication-related columns to the users table:
- password_hash: For email/password authentication (nullable for OAuth-only users)
- google_oauth_id: For Google OAuth integration (nullable)
- oauth_provider: Track which OAuth provider was used (nullable enum)
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '009'
down_revision: Union[str, None] = '008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add authentication columns to users table."""
    # Create oauth_provider enum type
    op.execute("CREATE TYPE oauth_provider AS ENUM ('google', 'github')")

    # Add password_hash column (nullable for OAuth-only users)
    op.add_column('users', sa.Column('password_hash', sa.String(255), nullable=True))

    # Add google_oauth_id column for OAuth integration
    op.add_column('users', sa.Column('google_oauth_id', sa.String(255), nullable=True))

    # Add oauth_provider column
    op.add_column('users', sa.Column('oauth_provider', sa.Enum('google', 'github', name='oauth_provider'), nullable=True))

    # Create index on google_oauth_id for OAuth lookups
    op.create_index('ix_users_google_oauth_id', 'users', ['google_oauth_id'], unique=False)


def downgrade() -> None:
    """Remove authentication columns from users table."""
    op.drop_index('ix_users_google_oauth_id', table_name='users')
    op.drop_column('users', 'oauth_provider')
    op.drop_column('users', 'google_oauth_id')
    op.drop_column('users', 'password_hash')
    op.execute("DROP TYPE oauth_provider")
