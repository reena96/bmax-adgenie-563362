"""Create generation_jobs table

Revision ID: 007
Revises: 006
Create Date: 2025-11-15

This migration creates the generation_jobs table for tracking video/audio generation
tasks processed by external services (e.g., Replicate). Tracks job status, progress,
and generated media URLs.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '007'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create generation_jobs table with status and job type enums."""
    op.create_table(
        'generation_jobs',
        # Primary key: UUID generated server-side
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),

        # Foreign keys
        sa.Column('project_id', UUID(as_uuid=True), nullable=False),
        sa.Column('script_id', UUID(as_uuid=True), nullable=False),

        # Job status: queued → processing → completed/failed
        sa.Column('status',
                  sa.Enum('queued', 'processing', 'completed', 'failed', name='generation_job_status'),
                  nullable=False, server_default='queued'),

        # Job type: visual_generation, audio_generation, video_composition, final_export
        sa.Column('job_type',
                  sa.Enum('visual_generation', 'audio_generation', 'video_composition', 'final_export',
                          name='generation_job_type'),
                  nullable=False),

        # External service job ID (e.g., Replicate prediction ID)
        sa.Column('replicate_job_id', sa.String(255), nullable=True),

        # Progress tracking (0-100)
        sa.Column('progress_percentage', sa.Integer, nullable=False, server_default='0'),

        # Error information (populated if status = 'failed')
        sa.Column('error_message', sa.Text, nullable=True),

        # Generated output URL (S3 or external URL)
        sa.Column('generated_video_url', sa.String(512), nullable=True),

        # Timing information
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

        # Foreign key constraints
        sa.ForeignKeyConstraint(['project_id'], ['ad_projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['script_id'], ['scripts.id'], ondelete='CASCADE'),

        # Check constraint: progress_percentage between 0 and 100
        sa.CheckConstraint('progress_percentage >= 0 AND progress_percentage <= 100',
                           name='ck_generation_jobs_progress_percentage'),
    )

    # Composite index for filtering project's jobs by status
    op.create_index('ix_generation_jobs_project_id_status', 'generation_jobs', ['project_id', 'status'])

    # Composite index for finding jobs by status and creation time
    op.create_index('ix_generation_jobs_status_created_at', 'generation_jobs', ['status', 'created_at'])

    # Index on replicate_job_id for webhook lookups
    op.create_index('ix_generation_jobs_replicate_job_id', 'generation_jobs', ['replicate_job_id'])

    # Single indexes on foreign keys
    op.create_index('ix_generation_jobs_project_id', 'generation_jobs', ['project_id'])
    op.create_index('ix_generation_jobs_script_id', 'generation_jobs', ['script_id'])


def downgrade() -> None:
    """Drop generation_jobs table and its indexes."""
    op.drop_index('ix_generation_jobs_script_id', table_name='generation_jobs')
    op.drop_index('ix_generation_jobs_project_id', table_name='generation_jobs')
    op.drop_index('ix_generation_jobs_replicate_job_id', table_name='generation_jobs')
    op.drop_index('ix_generation_jobs_status_created_at', table_name='generation_jobs')
    op.drop_index('ix_generation_jobs_project_id_status', table_name='generation_jobs')
    op.drop_table('generation_jobs')
