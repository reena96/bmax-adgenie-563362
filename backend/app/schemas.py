"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str
    timestamp: datetime
    db_connected: bool
    redis_connected: bool


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    detail: str
    status_code: int


# Authentication schemas (Story 1.2)
class SignupRequest(BaseModel):
    """User signup request schema."""
    email: EmailStr
    name: str
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    """User login request schema."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response schema (excludes password_hash)."""
    id: UUID
    email: str
    name: str
    subscription_tier: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Token response schema for login/signup."""
    user: UserResponse
    access_token: str
    token_type: str = "bearer"


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""
    reset_token: str
    new_password: str = Field(..., min_length=8)


class GoogleCallbackRequest(BaseModel):
    """Google OAuth callback request schema."""
    code: str
    state: Optional[str] = None


class MessageResponse(BaseModel):
    """Generic message response schema."""
    message: str


# Legacy schemas (kept for backward compatibility)
class UserCreate(BaseModel):
    """User creation schema (Story 1.2)."""
    email: EmailStr
    name: str
    password: str


class BrandGuidelines(BaseModel):
    """Brand guidelines schema."""
    colors: Optional[list[str]] = Field(default=None, max_length=5)
    fonts: Optional[list[str]] = None
    tone: Optional[str] = None
    additional_assets: Optional[list[str]] = None


class BrandCreate(BaseModel):
    """Brand creation schema (Story 1.3)."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=500)
    brand_guidelines: Optional[BrandGuidelines] = None


class BrandUpdate(BaseModel):
    """Brand update schema (Story 1.3)."""
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=500)
    brand_guidelines: Optional[BrandGuidelines] = None


class BrandResponse(BaseModel):
    """Brand response schema (Story 1.3)."""
    id: UUID
    user_id: UUID
    title: str
    description: Optional[str] = None
    product_images: list[str] = []
    brand_guidelines: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BrandListItem(BaseModel):
    """Brand list item schema for paginated listing."""
    id: UUID
    title: str
    thumbnail_url: Optional[str] = None
    image_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class PaginationMeta(BaseModel):
    """Pagination metadata schema."""
    page: int
    limit: int
    total: int
    has_more: bool


class BrandListResponse(BaseModel):
    """Paginated brand list response schema."""
    brands: list[BrandListItem]
    pagination: PaginationMeta


class AdProjectCreate(BaseModel):
    """Ad project creation schema (Story 1.4)."""
    brand_id: UUID
    ad_details: Optional[dict] = None


class AdProjectResponse(BaseModel):
    """Ad project response schema (Story 1.4)."""
    id: UUID
    user_id: UUID
    brand_id: UUID
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
