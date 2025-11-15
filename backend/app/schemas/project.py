"""
Project schemas (Pydantic models).

Request and response schemas for ad project-related endpoints.
Full implementation will be added in a future story.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    """Base project schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""
    brand_id: int


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = None


class ProjectResponse(ProjectBase):
    """Schema for project response."""
    id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
