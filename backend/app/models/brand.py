"""
Brand model for storing brand information and guidelines.

SQLAlchemy model mapping to the 'brands' table.
"""
import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Brand(Base):
    """Brand model with JSONB for product images and brand guidelines."""

    __tablename__ = "brands"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())

    # Foreign key to users
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Brand information
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # JSONB columns for flexible data
    # product_images: Array of S3 URLs
    product_images = Column(JSONB, nullable=False, server_default='[]')

    # brand_guidelines: Object with colors, fonts, tone, assets
    brand_guidelines = Column(JSONB, nullable=False, server_default='{}')

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="brands")
    ad_projects = relationship("AdProject", back_populates="brand", cascade="all, delete-orphan")
    lora_model = relationship("LoRAModel", back_populates="brand", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Brand(id={self.id}, title={self.title}, user_id={self.user_id})>"
