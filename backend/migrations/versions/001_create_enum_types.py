"""Create PostgreSQL enum types

Revision ID: 001
Revises:
Create Date: 2025-11-15

This migration creates all PostgreSQL enum types used by the application.
These enums must be created before any tables that reference them.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all enum types for the application."""

    # User subscription types
    op.execute("""
        CREATE TYPE subscription_type AS ENUM (
            'free',
            'pro',
            'enterprise'
        )
    """)

    # Ad Project status lifecycle
    op.execute("""
        CREATE TYPE ad_project_status AS ENUM (
            'initial',
            'chat_in_progress',
            'script_generated',
            'script_approved',
            'video_generating',
            'completed',
            'failed'
        )
    """)

    # Chat message roles
    op.execute("""
        CREATE TYPE chat_role AS ENUM (
            'user',
            'assistant'
        )
    """)

    # Generation job status
    op.execute("""
        CREATE TYPE generation_job_status AS ENUM (
            'queued',
            'processing',
            'completed',
            'failed'
        )
    """)

    # Generation job types
    op.execute("""
        CREATE TYPE generation_job_type AS ENUM (
            'visual_generation',
            'audio_generation',
            'video_composition',
            'final_export'
        )
    """)

    # LoRA model training status
    op.execute("""
        CREATE TYPE lora_training_status AS ENUM (
            'not_started',
            'in_progress',
            'completed',
            'failed'
        )
    """)


def downgrade() -> None:
    """Drop all enum types."""
    # Drop in reverse order (though order doesn't matter for enums without dependencies)
    op.execute("DROP TYPE IF EXISTS lora_training_status")
    op.execute("DROP TYPE IF EXISTS generation_job_type")
    op.execute("DROP TYPE IF EXISTS generation_job_status")
    op.execute("DROP TYPE IF EXISTS chat_role")
    op.execute("DROP TYPE IF EXISTS ad_project_status")
    op.execute("DROP TYPE IF EXISTS subscription_type")
