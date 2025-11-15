"""
LoRA Model metadata for brand-specific model training.

SQLAlchemy model mapping to the 'lora_models' table.
"""
import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class LoRAModel(Base):
    """LoRA model metadata with training status tracking."""

    __tablename__ = "lora_models"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())

    # Foreign key to brands (unique - one model per brand)
    brand_id = Column(UUID(as_uuid=True), ForeignKey('brands.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)

    # Model information
    model_name = Column(String(255), nullable=False)

    # HuggingFace model ID (set after successful training)
    huggingface_model_id = Column(String(255), nullable=True)

    # Training status enum
    training_status = Column(
        Enum('not_started', 'in_progress', 'completed', 'failed', name='lora_training_status'),
        nullable=False,
        server_default='not_started',
        index=True
    )

    # Training progress (0-100)
    training_progress = Column(Integer, nullable=False, server_default='0')

    # Number of training samples processed
    trained_samples_count = Column(Integer, nullable=False, server_default='0')

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    brand = relationship("Brand", back_populates="lora_model")

    # Check constraints
    __table_args__ = (
        CheckConstraint('training_progress >= 0 AND training_progress <= 100',
                        name='ck_lora_models_training_progress'),
        CheckConstraint('trained_samples_count >= 0',
                        name='ck_lora_models_trained_samples_count'),
    )

    def __repr__(self):
        return f"<LoRAModel(id={self.id}, brand_id={self.brand_id}, status={self.training_status}, progress={self.training_progress}%)>"
