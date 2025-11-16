"""
Pydantic schemas for authentication endpoints.

Request and response models for signup, login, token refresh, password reset, etc.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator
import re


# ============================================================================
# Request Schemas
# ============================================================================

class SignupRequest(BaseModel):
    """Request schema for user signup."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="User password")
    name: str = Field(..., min_length=1, max_length=255, description="User full name")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "name": "John Doe"
            }
        }


class LoginRequest(BaseModel):
    """Request schema for user login."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!"
            }
        }


class RefreshTokenRequest(BaseModel):
    """Request schema for token refresh."""
    refresh_token: str = Field(..., description="Refresh token to exchange for new access token")

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class PasswordResetRequest(BaseModel):
    """Request schema for requesting password reset."""
    email: EmailStr = Field(..., description="Email address to send reset code to")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class PasswordResetConfirm(BaseModel):
    """Request schema for confirming password reset with code."""
    email: EmailStr = Field(..., description="Email address")
    reset_token: str = Field(..., min_length=6, max_length=6, description="6-digit reset code")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")

    @validator('reset_token')
    def validate_reset_token_format(cls, v):
        """Validate that reset token is 6 digits."""
        if not re.match(r'^\d{6}$', v):
            raise ValueError('Reset token must be exactly 6 digits')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "reset_token": "123456",
                "new_password": "NewSecurePass123!"
            }
        }


class GoogleSignInRequest(BaseModel):
    """Request schema for Google OAuth sign-in."""
    id_token: str = Field(..., description="Google ID token from client library")

    class Config:
        json_schema_extra = {
            "example": {
                "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjE2NTY..."
            }
        }


# ============================================================================
# Response Schemas
# ============================================================================

class UserResponse(BaseModel):
    """User data response (never includes password_hash)."""
    id: str
    email: str
    name: str
    subscription_tier: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2 (was orm_mode in v1)
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "name": "John Doe",
                "subscription_tier": "free",
                "created_at": "2025-11-16T10:30:00Z",
                "updated_at": "2025-11-16T10:30:00Z"
            }
        }


class SignupResponse(BaseModel):
    """Response schema for successful signup."""
    id: str
    email: str
    name: str
    subscription_tier: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "name": "John Doe",
                "subscription_tier": "free"
            }
        }


class LoginResponse(BaseModel):
    """Response schema for successful login."""
    access_token: str
    refresh_token: str
    user: UserResponse

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "user": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "email": "user@example.com",
                    "name": "John Doe",
                    "subscription_tier": "free",
                    "created_at": "2025-11-16T10:30:00Z",
                    "updated_at": "2025-11-16T10:30:00Z"
                }
            }
        }


class RefreshTokenResponse(BaseModel):
    """Response schema for token refresh."""
    access_token: str
    refresh_token: str

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Operation completed successfully"
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: str
    code: str
    timestamp: str

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Invalid credentials",
                "code": "INVALID_CREDENTIALS",
                "timestamp": "2025-11-16T10:30:00Z"
            }
        }
