"""
Asset schemas (Pydantic models).

Request and response schemas for asset-related endpoints including
file uploads and presigned URL generation.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class AssetBase(BaseModel):
    """Base asset schema."""
    original_filename: str = Field(..., min_length=1, max_length=255)
    asset_type: str = Field(..., min_length=1, max_length=50)


class AssetCreate(BaseModel):
    """Schema for creating an asset record."""
    user_id: UUID
    s3_key: str = Field(..., min_length=1)
    original_filename: str = Field(..., min_length=1, max_length=255)
    file_size: int = Field(..., gt=0)
    mime_type: str = Field(..., min_length=1, max_length=100)
    asset_type: str = Field(..., min_length=1, max_length=50)
    asset_metadata: Optional[Dict[str, Any]] = None


class AssetResponse(BaseModel):
    """Schema for asset response."""
    id: UUID
    user_id: UUID
    s3_key: str
    original_filename: str
    file_size: int
    mime_type: str
    asset_type: str
    asset_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssetUploadResponse(BaseModel):
    """Schema for file upload response."""
    asset_id: UUID
    filename: str
    s3_url: str
    presigned_url: str
    size_bytes: int
    mime_type: str
    asset_type: str
    created_at: datetime


class AssetListResponse(BaseModel):
    """Schema for listing assets."""
    assets: list[AssetResponse]
    total: int
    page: int
    page_size: int


class PresignedUrlRequest(BaseModel):
    """Schema for presigned URL generation request."""
    expiration_hours: int = Field(default=24, ge=1, le=168)  # 1 hour to 7 days

    @field_validator('expiration_hours')
    @classmethod
    def validate_expiration(cls, v: int) -> int:
        """Validate expiration hours are within allowed range."""
        if v < 1 or v > 168:
            raise ValueError("Expiration hours must be between 1 and 168 (7 days)")
        return v


class PresignedUrlResponse(BaseModel):
    """Schema for presigned URL response."""
    asset_id: UUID
    presigned_url: str
    expiration_at: str
    original_filename: str
    size_bytes: int


class MultipleUploadResponse(BaseModel):
    """Schema for multiple file upload response."""
    uploads: list[AssetUploadResponse]
    total_uploaded: int
    total_size_bytes: int
