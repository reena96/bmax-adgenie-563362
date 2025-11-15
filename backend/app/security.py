"""
Security utilities for password hashing, JWT tokens, and authentication.
Provides functions for bcrypt password hashing and JWT token management.
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User
from app.redis_client import get_redis_client

# Password hashing context with bcrypt (salt_rounds=10)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=10)

# HTTP Bearer token security scheme
security = HTTPBearer()


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with salt rounds >= 10.

    Args:
        password: Plain text password to hash

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a bcrypt hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password meets strength requirements.
    Requirements: min 8 chars, at least 1 uppercase, 1 lowercase, 1 digit

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"

    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"

    return True, ""


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with HS256 algorithm.

    Args:
        data: Dictionary containing token claims (should include 'sub' for user_id, 'email')
        expires_delta: Optional custom expiration time delta

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()
    })

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string to verify

    Returns:
        Decoded token payload dictionary

    Raises:
        HTTPException: If token is invalid or expired (401 Unauthorized)
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise credentials_exception


def hash_token(token: str) -> str:
    """
    Create SHA-256 hash of a token for storage in database.

    Args:
        token: Token string to hash

    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(token.encode()).hexdigest()


def is_token_blacklisted(token: str) -> bool:
    """
    Check if a token is blacklisted in Redis (after logout).

    Args:
        token: Token string to check

    Returns:
        True if token is blacklisted, False otherwise
    """
    redis_client = get_redis_client()
    token_hash = hash_token(token)
    return redis_client.exists(f"blacklist:{token_hash}") > 0


def blacklist_token(token: str, expire_seconds: int = 900) -> None:
    """
    Add a token to the blacklist in Redis (for logout).
    Token blacklist expires after expire_seconds to prevent memory bloat.

    Args:
        token: Token string to blacklist
        expire_seconds: Seconds until blacklist entry expires (default 15 min = 900 sec)
    """
    redis_client = get_redis_client()
    token_hash = hash_token(token)
    redis_client.setex(f"blacklist:{token_hash}", expire_seconds, "1")


def generate_reset_token() -> str:
    """
    Generate a secure random token for password reset (32 bytes, URL-safe).

    Returns:
        URL-safe reset token string
    """
    return secrets.token_urlsafe(32)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency to get the current authenticated user from JWT token.
    Validates token, checks blacklist, and loads user from database.

    Args:
        credentials: HTTP Bearer credentials from request header
        db: Database session

    Returns:
        User object for the authenticated user

    Raises:
        HTTPException: If token is invalid, expired, blacklisted, or user not found (401)
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials

    # Check if token is blacklisted (after logout)
    if is_token_blacklisted(token):
        raise credentials_exception

    # Verify and decode token
    payload = verify_token(token)
    user_id: str = payload.get("sub")

    if user_id is None:
        raise credentials_exception

    # Load user from database
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise credentials_exception

    return user
