"""
Authentication models for refresh tokens and password reset tokens.

SQLAlchemy models for JWT refresh token management and password reset flow.
"""
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class RefreshToken(Base):
    """
    Refresh token model for JWT token rotation.

    Stores hashed refresh tokens (not plaintext) for security.
    Tokens can be revoked by setting revoked_at timestamp.
    """

    __tablename__ = "refresh_tokens"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())

    # Foreign key to users table
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Token hash (stored hashed, not plaintext)
    token_hash = Column(String(255), nullable=False)

    # Expiration tracking
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)

    # Revocation tracking (NULL = active, timestamp = revoked)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    user = relationship("User", backref="refresh_tokens")

    def __repr__(self):
        status = "revoked" if self.revoked_at else "active"
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, status={status})>"


class PasswordResetToken(Base):
    """
    Password reset token model for password reset flow.

    Stores hashed reset tokens (6-digit codes) with 1-hour expiration.
    Tokens are single-use (marked with used_at timestamp).
    """

    __tablename__ = "password_reset_tokens"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())

    # Foreign key to users table
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Token hash (6-digit code hashed for security)
    token_hash = Column(String(255), nullable=False)

    # Expiration tracking (1-hour expiry)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)

    # Single-use tracking (NULL = unused, timestamp = used)
    used_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    user = relationship("User", backref="password_reset_tokens")

    def __repr__(self):
        status = "used" if self.used_at else "unused"
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id}, status={status})>"
