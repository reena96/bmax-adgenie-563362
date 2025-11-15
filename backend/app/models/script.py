"""
Script model for generated ad scripts.

SQLAlchemy model mapping to the 'scripts' table.
"""
import uuid
from sqlalchemy import Column, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Script(Base):
    """Script model with scenes stored as JSONB."""

    __tablename__ = "scripts"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())

    # Foreign key to ad_projects (unique - one script per project)
    project_id = Column(UUID(as_uuid=True), ForeignKey('ad_projects.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)

    # Script content
    storyline = Column(Text, nullable=False)

    # Scenes array stored as JSONB
    scenes = Column(JSONB, nullable=False, server_default='[]')

    # Optional voiceover text
    voiceover_text = Column(Text, nullable=True)

    # Approval timestamp
    approved_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    project = relationship("AdProject", back_populates="script")
    generation_jobs = relationship("GenerationJob", back_populates="script", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Script(id={self.id}, project_id={self.project_id}, approved={self.approved_at is not None})>"
