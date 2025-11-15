"""
Generation Job model for tracking video/audio generation tasks.

SQLAlchemy model mapping to the 'generation_jobs' table.
"""
import uuid
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Enum, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class GenerationJob(Base):
    """Generation job model for tracking media generation progress."""

    __tablename__ = "generation_jobs"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())

    # Foreign keys
    project_id = Column(UUID(as_uuid=True), ForeignKey('ad_projects.id', ondelete='CASCADE'), nullable=False, index=True)
    script_id = Column(UUID(as_uuid=True), ForeignKey('scripts.id', ondelete='CASCADE'), nullable=False, index=True)

    # Job status enum
    status = Column(
        Enum('queued', 'processing', 'completed', 'failed', name='generation_job_status'),
        nullable=False,
        server_default='queued',
        index=True
    )

    # Job type enum
    job_type = Column(
        Enum('visual_generation', 'audio_generation', 'video_composition', 'final_export',
             name='generation_job_type'),
        nullable=False
    )

    # External service job ID (e.g., Replicate prediction ID)
    replicate_job_id = Column(String(255), nullable=True, index=True)

    # Progress tracking (0-100)
    progress_percentage = Column(Integer, nullable=False, server_default='0')

    # Error information
    error_message = Column(Text, nullable=True)

    # Generated output URL
    generated_video_url = Column(String(512), nullable=True)

    # Timing information
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    project = relationship("AdProject", back_populates="generation_jobs")
    script = relationship("Script", back_populates="generation_jobs")

    # Check constraint for progress percentage
    __table_args__ = (
        CheckConstraint('progress_percentage >= 0 AND progress_percentage <= 100',
                        name='ck_generation_jobs_progress_percentage'),
    )

    def __repr__(self):
        return f"<GenerationJob(id={self.id}, status={self.status}, job_type={self.job_type}, progress={self.progress_percentage}%)>"
