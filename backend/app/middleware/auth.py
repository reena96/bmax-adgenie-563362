"""
Authentication middleware for JWT token verification.

Provides FastAPI dependencies for protecting routes with JWT authentication.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session

from app.database import get_db
from app.utils.jwt import verify_access_token
from app.models.user import User

# HTTP Bearer token scheme for extracting tokens from Authorization header
security = HTTPBearer()


def verify_jwt_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> dict:
    """
    FastAPI dependency to verify JWT token and extract user information.

    Extracts token from Authorization: Bearer {token} header,
    validates signature and expiration, and returns payload.

    Args:
        credentials: HTTP Authorization credentials (automatically extracted by FastAPI)
        db: Database session (for future user validation)

    Returns:
        Dictionary containing token payload with user_id, email, subscription_tier

    Raises:
        HTTPException 401: If token is missing, invalid, expired, or user not found

    Usage:
        @router.get("/protected")
        async def protected_route(token_data: dict = Depends(verify_jwt_token)):
            user_id = token_data["sub"]
            return {"user_id": user_id}
    """
    token = credentials.credentials

    try:
        # Verify and decode token
        payload = verify_access_token(token)

        # Extract user_id from payload
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Return token payload for route handlers
        return payload

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    token_data: dict = Depends(verify_jwt_token),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency to get current authenticated user from database.

    Verifies JWT token and fetches the corresponding user from database.
    Returns 401 if user is deleted or not found.

    Args:
        token_data: Token payload from verify_jwt_token dependency
        db: Database session

    Returns:
        User model instance for authenticated user

    Raises:
        HTTPException 401: If user not found or deleted

    Usage:
        @router.get("/me")
        async def get_me(current_user: User = Depends(get_current_user)):
            return {"email": current_user.email}
    """
    user_id = token_data.get("sub")

    # Fetch user from database
    user = db.query(User).filter(
        User.id == user_id,
        User.deleted_at.is_(None)  # Exclude soft-deleted users
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deleted",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    FastAPI dependency for optional authentication.

    Returns User if valid token is provided, None if no token.
    Useful for endpoints that work differently for authenticated vs anonymous users.

    Args:
        credentials: Optional HTTP Authorization credentials
        db: Database session

    Returns:
        User model instance if authenticated, None if not

    Usage:
        @router.get("/content")
        async def get_content(user: Optional[User] = Depends(get_current_user_optional)):
            if user:
                return {"message": f"Hello {user.name}"}
            return {"message": "Hello guest"}
    """
    if not credentials:
        return None

    try:
        token = credentials.credentials
        payload = verify_access_token(token)
        user_id = payload.get("sub")

        if not user_id:
            return None

        user = db.query(User).filter(
            User.id == user_id,
            User.deleted_at.is_(None)
        ).first()

        return user

    except (JWTError, Exception):
        return None
