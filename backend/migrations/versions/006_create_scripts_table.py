"""Create scripts table

Revision ID: 006
Revises: 005
Create Date: 2025-11-15

This migration creates the scripts table for storing generated ad scripts with scenes.
Each project can have at most one script (unique constraint on project_id).
Scenes are stored as JSONB array with visual/audio prompts and generated media URLs.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create scripts table with JSONB scenes and unique project constraint."""
    op.create_table(
        'scripts',
        # Primary key: UUID generated server-side
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),

        # Foreign key to ad_projects with UNIQUE constraint (one script per project)
        sa.Column('project_id', UUID(as_uuid=True), nullable=False, unique=True),

        # Script content
        sa.Column('storyline', sa.Text, nullable=False),

        # Scenes array stored as JSONB
        # Each scene: {sceneNumber, description, duration, visualPrompt, audioPrompt,
        #             generatedVideoUrl?, generatedAudioUrl?}
        sa.Column('scenes', JSONB, nullable=False, server_default='[]'),

        # Optional voiceover text for the entire ad
        sa.Column('voiceover_text', sa.Text, nullable=True),

        # Approval timestamp (nullable - set when script is approved by user)
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),

        # Timestamps (UTC)
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

        # Foreign key constraint with CASCADE delete
        sa.ForeignKeyConstraint(['project_id'], ['ad_projects.id'], ondelete='CASCADE'),
    )

    # Unique index on project_id (enforces one script per project)
    op.create_index('ix_scripts_project_id', 'scripts', ['project_id'], unique=True)

    # Index on approved_at for finding approved/pending scripts
    op.create_index('ix_scripts_approved_at', 'scripts', ['approved_at'])


def downgrade() -> None:
    """Drop scripts table and its indexes."""
    op.drop_index('ix_scripts_approved_at', table_name='scripts')
    op.drop_index('ix_scripts_project_id', table_name='scripts')
    op.drop_table('scripts')
