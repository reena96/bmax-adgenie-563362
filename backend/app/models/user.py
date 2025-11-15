"""
User model for authentication and account management.

SQLAlchemy model mapping to the 'users' table.
"""
import uuid
from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """User account model with subscription tiers and soft-delete support."""

    __tablename__ = "users"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())

    # Authentication and profile
    email = Column(String(255), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)

    # Subscription type enum
    subscription_type = Column(
        Enum('free', 'pro', 'enterprise', name='subscription_type'),
        nullable=False,
        server_default='free'
    )

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Soft delete support
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    brands = relationship("Brand", back_populates="user", cascade="all, delete-orphan")
    ad_projects = relationship("AdProject", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, subscription_type={self.subscription_type})>"
