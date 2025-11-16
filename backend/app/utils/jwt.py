"""
JWT token utilities for access and refresh token management.

Uses python-jose library for JWT creation and validation.
Implements token rotation and expiration handling.
"""
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from jose import jwt, JWTError

# JWT Configuration from environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # As per AC-3
REFRESH_TOKEN_EXPIRE_DAYS = 7  # As per AC-3


def create_access_token(user_id: str, email: str, subscription_tier: str) -> str:
    """
    Create a JWT access token with 15-minute expiration.

    Args:
        user_id: User UUID as string
        email: User email address
        subscription_tier: User subscription tier (free, pro, enterprise)

    Returns:
        Encoded JWT access token string

    Token Payload:
        - sub: User ID (subject)
        - email: User email
        - subscription_tier: Subscription level
        - iat: Issued at timestamp
        - exp: Expiration timestamp (15 minutes from now)

    Example:
        >>> token = create_access_token("user-id-123", "user@example.com", "free")
        >>> payload = verify_token(token)
        >>> payload["sub"] == "user-id-123"
        True
    """
    now = datetime.utcnow()
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(user_id),  # Subject (user ID)
        "email": email,
        "subscription_tier": subscription_tier,
        "iat": now,  # Issued at
        "exp": expire  # Expiration
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: str) -> tuple[str, str]:
    """
    Create a JWT refresh token with 7-day expiration.

    Args:
        user_id: User UUID as string

    Returns:
        Tuple of (encoded_token: str, token_id: str)
        - encoded_token: JWT refresh token string
        - token_id: Unique token ID (jti) for database storage

    Token Payload:
        - sub: User ID (subject)
        - type: Token type ("refresh")
        - jti: Unique token ID (for revocation tracking)
        - iat: Issued at timestamp
        - exp: Expiration timestamp (7 days from now)

    Example:
        >>> token, jti = create_refresh_token("user-id-123")
        >>> payload = verify_token(token)
        >>> payload["type"] == "refresh"
        True
    """
    now = datetime.utcnow()
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    token_id = str(uuid.uuid4())  # Unique token ID for tracking

    payload = {
        "sub": str(user_id),  # Subject (user ID)
        "type": "refresh",
        "jti": token_id,  # JWT ID for revocation
        "iat": now,  # Issued at
        "exp": expire  # Expiration
    }

    encoded_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_token, token_id


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode a JWT token (access or refresh).

    Args:
        token: JWT token string to verify

    Returns:
        Decoded token payload as dictionary

    Raises:
        JWTError: If token is invalid, expired, or has bad signature

    Example:
        >>> token = create_access_token("user-id", "user@example.com", "free")
        >>> payload = verify_token(token)
        >>> "sub" in payload
        True
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise JWTError(f"Invalid token: {str(e)}")


def verify_access_token(token: str) -> Dict[str, Any]:
    """
    Verify an access token and extract payload.

    Args:
        token: JWT access token string

    Returns:
        Decoded token payload

    Raises:
        JWTError: If token is invalid, expired, or not an access token

    Example:
        >>> token = create_access_token("user-id", "user@example.com", "free")
        >>> payload = verify_access_token(token)
        >>> payload["email"] == "user@example.com"
        True
    """
    payload = verify_token(token)

    # Ensure it's not a refresh token
    if payload.get("type") == "refresh":
        raise JWTError("Invalid token type: expected access token")

    return payload


def verify_refresh_token(token: str) -> Dict[str, Any]:
    """
    Verify a refresh token and extract payload.

    Args:
        token: JWT refresh token string

    Returns:
        Decoded token payload

    Raises:
        JWTError: If token is invalid, expired, or not a refresh token

    Example:
        >>> token, jti = create_refresh_token("user-id")
        >>> payload = verify_refresh_token(token)
        >>> payload["type"] == "refresh"
        True
    """
    payload = verify_token(token)

    # Ensure it's a refresh token
    if payload.get("type") != "refresh":
        raise JWTError("Invalid token type: expected refresh token")

    return payload


def get_token_expiration(token: str) -> Optional[datetime]:
    """
    Extract expiration timestamp from a token without full verification.

    Args:
        token: JWT token string

    Returns:
        Expiration datetime or None if token is malformed

    Example:
        >>> token = create_access_token("user-id", "user@example.com", "free")
        >>> exp = get_token_expiration(token)
        >>> exp is not None
        True
    """
    try:
        # Decode without verification to extract expiration
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_signature": False})
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            return datetime.fromtimestamp(exp_timestamp)
        return None
    except Exception:
        return None


def is_token_expired(token: str) -> bool:
    """
    Check if a token is expired without raising an exception.

    Args:
        token: JWT token string

    Returns:
        True if expired, False if still valid or malformed

    Example:
        >>> token = create_access_token("user-id", "user@example.com", "free")
        >>> is_token_expired(token)
        False
    """
    exp = get_token_expiration(token)
    if exp is None:
        return True  # Treat malformed tokens as expired
    return datetime.utcnow() > exp
