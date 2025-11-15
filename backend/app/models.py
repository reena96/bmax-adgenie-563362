"""
SQLAlchemy ORM models for the database schema.
Implements all 8 tables: users, brands, lora_models, ad_projects,
chat_messages, scripts, generation_jobs, sessions.
"""
from sqlalchemy import (
    Column, String, Integer, DateTime, ForeignKey, Boolean, Text, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class User(Base):
    """User model for authentication and subscription management."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=True)  # Nullable for OAuth-only users
    google_sub = Column(String(255), unique=True, nullable=True, index=True)  # Google OAuth user ID
    subscription_tier = Column(String(50), default="free")  # free, starter, pro, enterprise
    credits = Column(Integer, default=0)
    free_videos_used = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    brands = relationship("Brand", back_populates="user", cascade="all, delete-orphan")
    ad_projects = relationship("AdProject", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    password_resets = relationship("PasswordReset", back_populates="user", cascade="all, delete-orphan")


class Brand(Base):
    """Brand model for storing brand information and guidelines."""
    __tablename__ = "brands"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    product_images = Column(JSONB)  # Array of S3 URLs
    brand_guidelines = Column(JSONB)  # JSON object with brand details
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="brands")
    lora_models = relationship("LoraModel", back_populates="brand", cascade="all, delete-orphan")
    ad_projects = relationship("AdProject", back_populates="brand", cascade="all, delete-orphan")


class LoraModel(Base):
    """LoRA model tracking for brand-specific fine-tuned models."""
    __tablename__ = "lora_models"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True)  # training, completed, failed
    model_url = Column(String(500))  # S3 or external URL to trained model
    preview_image_url = Column(String(500))  # Preview image generated during training
    training_job_id = Column(String(255))  # External training service job ID
    user_approved = Column(Boolean, default=False)
    error_message = Column(Text)
    trained_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    brand = relationship("Brand", back_populates="lora_models")


class AdProject(Base):
    """Ad project model for tracking individual ad generation projects."""
    __tablename__ = "ad_projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True)  # draft, generating, completed, failed
    ad_details = Column(JSONB)  # JSON with project specifications
    zapcut_project_id = Column(String(255))  # External Zapcut project ID
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="ad_projects")
    brand = relationship("Brand", back_populates="ad_projects")
    chat_messages = relationship("ChatMessage", back_populates="ad_project", cascade="all, delete-orphan")
    scripts = relationship("Script", back_populates="ad_project", cascade="all, delete-orphan")
    generation_jobs = relationship("GenerationJob", back_populates="ad_project", cascade="all, delete-orphan")


class ChatMessage(Base):
    """Chat message model for AI conversation history."""
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ad_project_id = Column(UUID(as_uuid=True), ForeignKey("ad_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    ad_project = relationship("AdProject", back_populates="chat_messages")


class Script(Base):
    """Script model for storing approved video scripts."""
    __tablename__ = "scripts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ad_project_id = Column(UUID(as_uuid=True), ForeignKey("ad_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    storyline = Column(Text, nullable=False)
    scenes = Column(JSONB, nullable=False)  # Array of scene objects
    approved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    ad_project = relationship("AdProject", back_populates="scripts")


class GenerationJob(Base):
    """Generation job model for tracking async video generation tasks."""
    __tablename__ = "generation_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ad_project_id = Column(UUID(as_uuid=True), ForeignKey("ad_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    job_type = Column(String(100), nullable=False)  # scene_1, scene_2, voiceover, music, composite
    status = Column(String(50), nullable=False, index=True)  # pending, processing, completed, failed
    replicate_job_id = Column(String(255))  # External service job ID
    input_params = Column(JSONB)  # Input parameters for the job
    output_url = Column(String(500))  # S3 URL to generated output
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    ad_project = relationship("AdProject", back_populates="generation_jobs")


class Session(Base):
    """Session model for user authentication token management."""
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(500), unique=True, nullable=False, index=True)  # SHA-256 hash of JWT token
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="sessions")


class PasswordReset(Base):
    """Password reset model for tracking reset tokens."""
    __tablename__ = "password_resets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)  # Reset token (URL-safe)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    used_at = Column(DateTime(timezone=True), nullable=True)  # Set when reset is completed
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="password_resets")


# Create composite indexes for common queries
Index("idx_generation_jobs_project_status", GenerationJob.ad_project_id, GenerationJob.status)
Index("idx_ad_projects_user_status", AdProject.user_id, AdProject.status)
Index("idx_brands_user", Brand.user_id)
