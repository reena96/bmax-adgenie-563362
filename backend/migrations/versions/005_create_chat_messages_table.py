"""Create chat_messages table

Revision ID: 005
Revises: 004
Create Date: 2025-11-15

This migration creates the chat_messages table for storing conversation history
between users and the AI assistant. Messages are associated with ad projects and
deleted when the project is deleted (CASCADE).
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create chat_messages table with role enum and CASCADE delete."""
    op.create_table(
        'chat_messages',
        # Primary key: UUID generated server-side
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),

        # Foreign key to ad_projects (CASCADE delete - remove messages when project is deleted)
        sa.Column('project_id', UUID(as_uuid=True), nullable=False),

        # Message role: 'user' or 'assistant'
        sa.Column('role',
                  sa.Enum('user', 'assistant', name='chat_role'),
                  nullable=False),

        # Message content
        sa.Column('content', sa.Text, nullable=False),

        # Message timestamp (when the message was sent)
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

        # Created timestamp (audit trail)
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

        # Foreign key constraint with CASCADE delete
        sa.ForeignKeyConstraint(['project_id'], ['ad_projects.id'], ondelete='CASCADE'),
    )

    # Composite index for retrieving conversation history ordered by timestamp
    op.create_index('ix_chat_messages_project_id_timestamp', 'chat_messages', ['project_id', 'timestamp'])

    # Single index on project_id for foreign key lookups
    op.create_index('ix_chat_messages_project_id', 'chat_messages', ['project_id'])


def downgrade() -> None:
    """Drop chat_messages table and its indexes."""
    op.drop_index('ix_chat_messages_project_id', table_name='chat_messages')
    op.drop_index('ix_chat_messages_project_id_timestamp', table_name='chat_messages')
    op.drop_table('chat_messages')
