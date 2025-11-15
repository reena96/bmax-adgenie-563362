"""
Brand schemas (Pydantic models).

Request and response schemas for brand-related endpoints.
Full implementation will be added in a future story.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class BrandBase(BaseModel):
    """Base brand schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class BrandCreate(BrandBase):
    """Schema for creating a brand."""
    pass


class BrandUpdate(BaseModel):
    """Schema for updating a brand."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class BrandResponse(BrandBase):
    """Schema for brand response."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
