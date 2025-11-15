"""Create lora_models table

Revision ID: 008
Revises: 007
Create Date: 2025-11-15

This migration creates the lora_models table for tracking brand-specific LoRA model
training. Each brand can have at most one LoRA model (unique constraint on brand_id).
Tracks training status, progress, and HuggingFace model ID.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '008'
down_revision: Union[str, None] = '007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create lora_models table with training status enum and unique brand constraint."""
    op.create_table(
        'lora_models',
        # Primary key: UUID generated server-side
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),

        # Foreign key to brands with UNIQUE constraint (one model per brand)
        sa.Column('brand_id', UUID(as_uuid=True), nullable=False, unique=True),

        # Model information
        sa.Column('model_name', sa.String(255), nullable=False),

        # HuggingFace model ID (set after successful training)
        sa.Column('huggingface_model_id', sa.String(255), nullable=True),

        # Training status: not_started → in_progress → completed/failed
        sa.Column('training_status',
                  sa.Enum('not_started', 'in_progress', 'completed', 'failed', name='lora_training_status'),
                  nullable=False, server_default='not_started'),

        # Training progress (0-100)
        sa.Column('training_progress', sa.Integer, nullable=False, server_default='0'),

        # Number of training samples processed
        sa.Column('trained_samples_count', sa.Integer, nullable=False, server_default='0'),

        # Timestamps (UTC)
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

        # Foreign key constraint with CASCADE delete
        sa.ForeignKeyConstraint(['brand_id'], ['brands.id'], ondelete='CASCADE'),

        # Check constraints for valid ranges
        sa.CheckConstraint('training_progress >= 0 AND training_progress <= 100',
                           name='ck_lora_models_training_progress'),
        sa.CheckConstraint('trained_samples_count >= 0',
                           name='ck_lora_models_trained_samples_count'),
    )

    # Unique index on brand_id (enforces one model per brand)
    op.create_index('ix_lora_models_brand_id', 'lora_models', ['brand_id'], unique=True)

    # Index on training_status for filtering models by status
    op.create_index('ix_lora_models_training_status', 'lora_models', ['training_status'])


def downgrade() -> None:
    """Drop lora_models table and its indexes."""
    op.drop_index('ix_lora_models_training_status', table_name='lora_models')
    op.drop_index('ix_lora_models_brand_id', table_name='lora_models')
    op.drop_table('lora_models')
