"""
Asset model for file uploads and S3 storage.

SQLAlchemy model mapping to the 'assets' table for tracking uploaded files
including brand images, generated videos, and other media assets.
"""
import uuid
from sqlalchemy import Column, String, DateTime, BigInteger, Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Asset(Base):
    """Asset model for tracking uploaded files in S3."""

    __tablename__ = "assets"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid()
    )

    # Foreign key to user
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # S3 storage information
    s3_key = Column(Text, nullable=False, unique=True, index=True)
    original_filename = Column(String(255), nullable=False)

    # File metadata
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)
    asset_type = Column(String(50), nullable=False, index=True)  # 'brand_image', 'generated_video', etc.

    # Additional metadata as JSON (flexible schema)
    # Using Column name override to avoid conflict with SQLAlchemy's metadata
    asset_metadata = Column('metadata', JSONB, nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    user = relationship("User", backref="assets")

    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_assets_user_created', 'user_id', 'created_at'),
        Index('idx_assets_type_created', 'asset_type', 'created_at'),
    )

    def __repr__(self):
        return (
            f"<Asset(id={self.id}, filename={self.original_filename}, "
            f"type={self.asset_type}, user_id={self.user_id})>"
        )
