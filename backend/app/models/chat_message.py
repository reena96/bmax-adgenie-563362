"""
Chat Message model for conversation history.

SQLAlchemy model mapping to the 'chat_messages' table.
"""
import uuid
from sqlalchemy import Column, Text, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class ChatMessage(Base):
    """Chat message model for storing user and assistant messages."""

    __tablename__ = "chat_messages"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())

    # Foreign key to ad_projects
    project_id = Column(UUID(as_uuid=True), ForeignKey('ad_projects.id', ondelete='CASCADE'), nullable=False, index=True)

    # Message role: 'user' or 'assistant'
    role = Column(
        Enum('user', 'assistant', name='chat_role'),
        nullable=False
    )

    # Message content
    content = Column(Text, nullable=False)

    # Message timestamp
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Created timestamp (audit trail)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    project = relationship("AdProject", back_populates="chat_messages")

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role={self.role}, project_id={self.project_id})>"
