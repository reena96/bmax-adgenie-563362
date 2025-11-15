"""Initial database schema

Revision ID: 001
Revises:
Create Date: 2025-11-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('subscription_tier', sa.String(50), server_default='free'),
        sa.Column('credits', sa.Integer, server_default='0'),
        sa.Column('free_videos_used', sa.Integer, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('ix_users_email', 'users', ['email'])

    # Create brands table
    op.create_table(
        'brands',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('product_images', JSONB),
        sa.Column('brand_guidelines', JSONB),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('ix_brands_user_id', 'brands', ['user_id'])
    op.create_index('idx_brands_user', 'brands', ['user_id'])

    # Create lora_models table
    op.create_table(
        'lora_models',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('brand_id', UUID(as_uuid=True), sa.ForeignKey('brands.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('model_url', sa.String(500)),
        sa.Column('preview_image_url', sa.String(500)),
        sa.Column('training_job_id', sa.String(255)),
        sa.Column('user_approved', sa.Boolean, server_default='false'),
        sa.Column('error_message', sa.Text),
        sa.Column('trained_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('ix_lora_models_brand_id', 'lora_models', ['brand_id'])
    op.create_index('ix_lora_models_status', 'lora_models', ['status'])

    # Create ad_projects table
    op.create_table(
        'ad_projects',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('brand_id', UUID(as_uuid=True), sa.ForeignKey('brands.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('ad_details', JSONB),
        sa.Column('zapcut_project_id', sa.String(255)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('ix_ad_projects_user_id', 'ad_projects', ['user_id'])
    op.create_index('ix_ad_projects_brand_id', 'ad_projects', ['brand_id'])
    op.create_index('ix_ad_projects_status', 'ad_projects', ['status'])
    op.create_index('idx_ad_projects_user_status', 'ad_projects', ['user_id', 'status'])

    # Create chat_messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('ad_project_id', UUID(as_uuid=True), sa.ForeignKey('ad_projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('ix_chat_messages_ad_project_id', 'chat_messages', ['ad_project_id'])

    # Create scripts table
    op.create_table(
        'scripts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('ad_project_id', UUID(as_uuid=True), sa.ForeignKey('ad_projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('storyline', sa.Text, nullable=False),
        sa.Column('scenes', JSONB, nullable=False),
        sa.Column('approved_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('ix_scripts_ad_project_id', 'scripts', ['ad_project_id'])

    # Create generation_jobs table
    op.create_table(
        'generation_jobs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('ad_project_id', UUID(as_uuid=True), sa.ForeignKey('ad_projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_type', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('replicate_job_id', sa.String(255)),
        sa.Column('input_params', JSONB),
        sa.Column('output_url', sa.String(500)),
        sa.Column('error_message', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('ix_generation_jobs_ad_project_id', 'generation_jobs', ['ad_project_id'])
    op.create_index('ix_generation_jobs_status', 'generation_jobs', ['status'])
    op.create_index('idx_generation_jobs_project_status', 'generation_jobs', ['ad_project_id', 'status'])

    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token', sa.String(500), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('ix_sessions_user_id', 'sessions', ['user_id'])
    op.create_index('ix_sessions_token', 'sessions', ['token'])


def downgrade() -> None:
    op.drop_table('sessions')
    op.drop_table('generation_jobs')
    op.drop_table('scripts')
    op.drop_table('chat_messages')
    op.drop_table('ad_projects')
    op.drop_table('lora_models')
    op.drop_table('brands')
    op.drop_table('users')
