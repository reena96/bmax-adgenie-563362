"""
Ad Project model for managing ad campaign projects.

SQLAlchemy model mapping to the 'ad_projects' table.
"""
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class AdProject(Base):
    """Ad project model with status tracking and conversation history."""

    __tablename__ = "ad_projects"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())

    # Foreign keys
    brand_id = Column(UUID(as_uuid=True), ForeignKey('brands.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='RESTRICT'), nullable=False, index=True)

    # Project status enum
    status = Column(
        Enum('initial', 'chat_in_progress', 'script_generated', 'script_approved',
             'video_generating', 'completed', 'failed', name='ad_project_status'),
        nullable=False,
        server_default='initial',
        index=True
    )

    # JSONB columns for flexible data
    # conversation_history: Array of message objects
    conversation_history = Column(JSONB, nullable=False, server_default='[]')

    # ad_details: Object with campaign details
    ad_details = Column(JSONB, nullable=False, server_default='{}')

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    brand = relationship("Brand", back_populates="ad_projects")
    user = relationship("User", back_populates="ad_projects")
    chat_messages = relationship("ChatMessage", back_populates="project", cascade="all, delete-orphan")
    script = relationship("Script", back_populates="project", uselist=False, cascade="all, delete-orphan")
    generation_jobs = relationship("GenerationJob", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AdProject(id={self.id}, status={self.status}, brand_id={self.brand_id})>"
