"""
Authentication routes for user signup, login, token management, and password reset.

Implements all authentication endpoints with JWT-based session management.
"""
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models.user import User
from app.models.auth import RefreshToken, PasswordResetToken
from app.schemas.auth import (
    SignupRequest, SignupResponse,
    LoginRequest, LoginResponse,
    RefreshTokenRequest, RefreshTokenResponse,
    PasswordResetRequest, PasswordResetConfirm,
    GoogleSignInRequest,
    UserResponse, MessageResponse
)
from app.utils.password import hash_password, verify_password, validate_password_strength
from app.utils.jwt import create_access_token, create_refresh_token, verify_refresh_token
from app.utils.email import normalize_email
from app.middleware.auth import get_current_user, verify_jwt_token

router = APIRouter()

# Rate limiting storage (in-memory for MVP, use Redis in production)
login_attempts: Dict[str, list] = {}
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


def check_rate_limit(ip_address: str) -> bool:
    """
    Check if IP address has exceeded rate limit for login attempts.

    Args:
        ip_address: Client IP address

    Returns:
        True if within rate limit, False if exceeded

    Rate limit: 5 failed attempts per 15 minutes per IP
    """
    if ip_address not in login_attempts:
        return True

    # Clean up old attempts (older than 15 minutes)
    cutoff_time = datetime.utcnow() - timedelta(minutes=LOCKOUT_DURATION_MINUTES)
    login_attempts[ip_address] = [
        attempt_time for attempt_time in login_attempts[ip_address]
        if attempt_time > cutoff_time
    ]

    # Check if exceeded limit
    return len(login_attempts[ip_address]) < MAX_LOGIN_ATTEMPTS


def record_failed_login(ip_address: str):
    """Record a failed login attempt for rate limiting."""
    if ip_address not in login_attempts:
        login_attempts[ip_address] = []
    login_attempts[ip_address].append(datetime.utcnow())


def hash_token(token: str) -> str:
    """Hash a token for secure database storage."""
    return hashlib.sha256(token.encode()).hexdigest()


# ============================================================================
# Authentication Endpoints
# ============================================================================

@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="User Signup",
    description="Create a new user account with email and password"
)
async def signup(
    request: SignupRequest,
    db: Session = Depends(get_db)
) -> SignupResponse:
    """
    Register a new user with email and password.

    Validation:
    - Email format (RFC 5322 compliant via Pydantic EmailStr)
    - Password strength requirements (see password utils)
    - Duplicate email check

    Returns:
        User data (id, email, name, subscription_tier)

    Raises:
        HTTPException 400: If validation fails or email already exists
    """
    # Normalize email (lowercase, strip whitespace)
    normalized_email = normalize_email(request.email)

    # Validate password strength
    is_valid, error_message = validate_password_strength(request.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )

    # Check if email already exists
    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password with bcrypt (12 rounds)
    password_hash = hash_password(request.password)

    # Create user
    new_user = User(
        email=normalized_email,
        name=request.name.strip(),
        password_hash=password_hash,
        subscription_type='free'
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Log signup event
        print(f"[AUTH] User signup successful: {new_user.email} (ID: {new_user.id})")

        return SignupResponse(
            id=str(new_user.id),
            email=new_user.email,
            name=new_user.name,
            subscription_tier=new_user.subscription_type
        )

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Authenticate user and return JWT access and refresh tokens"
)
async def login(
    request: LoginRequest,
    http_request: Request,
    db: Session = Depends(get_db)
) -> LoginResponse:
    """
    Authenticate user with email and password.

    On success:
    - Generates JWT access token (15-minute expiration)
    - Generates refresh token (7-day expiration)
    - Stores refresh token hash in database
    - Returns tokens and user data

    Rate limiting: 5 failed attempts per IP per 15 minutes

    Returns:
        Access token, refresh token, and user data

    Raises:
        HTTPException 401: If credentials are invalid
        HTTPException 429: If rate limit exceeded
    """
    # Get client IP for rate limiting
    client_ip = http_request.client.host if http_request.client else "unknown"

    # Check rate limit
    if not check_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed login attempts. Please try again in {LOCKOUT_DURATION_MINUTES} minutes."
        )

    # Normalize email
    normalized_email = normalize_email(request.email)

    # Find user by email (case-insensitive via normalization)
    user = db.query(User).filter(
        User.email == normalized_email,
        User.deleted_at.is_(None)  # Exclude soft-deleted users
    ).first()

    # Verify password
    if not user or not user.password_hash or not verify_password(request.password, user.password_hash):
        # Record failed attempt
        record_failed_login(client_ip)

        # Log failed login
        print(f"[AUTH] Login failed for email: {normalized_email} from IP: {client_ip}")

        # Generic error message (don't reveal if user exists)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Generate tokens
    access_token = create_access_token(
        user_id=str(user.id),
        email=user.email,
        subscription_tier=user.subscription_type
    )
    refresh_token_str, token_id = create_refresh_token(user_id=str(user.id))

    # Store refresh token hash in database
    token_hash = hash_token(refresh_token_str)
    expires_at = datetime.utcnow() + timedelta(days=7)

    refresh_token_record = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at
    )
    db.add(refresh_token_record)
    db.commit()

    # Log successful login
    print(f"[AUTH] Login successful: {user.email} (ID: {user.id})")

    # Return tokens and user data
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            subscription_tier=user.subscription_type,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    )


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh Access Token",
    description="Exchange refresh token for new access and refresh tokens"
)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
) -> RefreshTokenResponse:
    """
    Refresh access token using a valid refresh token.

    Token rotation: Old refresh token is revoked when new one is issued.

    Returns:
        New access token and new refresh token

    Raises:
        HTTPException 401: If refresh token is invalid, expired, or revoked
    """
    try:
        # Verify refresh token signature and expiration
        payload = verify_refresh_token(request.refresh_token)
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        # Hash the token to look up in database
        token_hash = hash_token(request.refresh_token)

        # Find refresh token in database
        stored_token = db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),  # Not revoked
            RefreshToken.expires_at > datetime.utcnow()  # Not expired
        ).first()

        if not stored_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found, expired, or revoked"
            )

        # Get user
        user = db.query(User).filter(
            User.id == user_id,
            User.deleted_at.is_(None)
        ).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        # Generate new tokens
        new_access_token = create_access_token(
            user_id=str(user.id),
            email=user.email,
            subscription_tier=user.subscription_type
        )
        new_refresh_token, new_token_id = create_refresh_token(user_id=str(user.id))

        # Revoke old refresh token
        stored_token.revoked_at = datetime.utcnow()

        # Store new refresh token
        new_token_hash = hash_token(new_refresh_token)
        new_expires_at = datetime.utcnow() + timedelta(days=7)
        new_refresh_record = RefreshToken(
            user_id=user.id,
            token_hash=new_token_hash,
            expires_at=new_expires_at
        )
        db.add(new_refresh_record)
        db.commit()

        print(f"[AUTH] Token refreshed for user: {user.email}")

        return RefreshTokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid refresh token: {str(e)}"
        )


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="User Logout",
    description="Logout user and revoke refresh token"
)
async def logout(
    token_data: dict = Depends(verify_jwt_token),
    db: Session = Depends(get_db)
) -> MessageResponse:
    """
    Logout user by revoking all active refresh tokens.

    Requires valid JWT access token in Authorization header.

    Returns:
        Success message

    Raises:
        HTTPException 401: If access token is invalid
    """
    user_id = token_data.get("sub")

    # Revoke all active refresh tokens for user
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked_at.is_(None)
    ).update({"revoked_at": datetime.utcnow()})

    db.commit()

    print(f"[AUTH] User logged out: {user_id}")

    return MessageResponse(message="Logged out successfully")


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current User",
    description="Get current authenticated user data"
)
async def get_me(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """
    Get current authenticated user information.

    Requires valid JWT access token in Authorization header.
    Allows frontend to verify session validity on app startup.

    Returns:
        Current user data

    Raises:
        HTTPException 401: If token is invalid or user deleted
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        name=current_user.name,
        subscription_tier=current_user.subscription_type,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


@router.post(
    "/request-password-reset",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Request Password Reset",
    description="Request a password reset code (6-digit code sent via email)"
)
async def request_password_reset(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
) -> MessageResponse:
    """
    Request password reset code.

    Generates 6-digit reset code with 1-hour expiration.
    For MVP: Logs code to console (real email service in production).

    Security: Returns success regardless of whether email exists.

    Returns:
        Success message (always, even if email not found)
    """
    normalized_email = normalize_email(request.email)

    # Find user
    user = db.query(User).filter(
        User.email == normalized_email,
        User.deleted_at.is_(None)
    ).first()

    if user:
        # Generate 6-digit code
        reset_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])

        # Hash code for storage
        code_hash = hash_token(reset_code)

        # Store in database
        expires_at = datetime.utcnow() + timedelta(hours=1)
        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=code_hash,
            expires_at=expires_at
        )
        db.add(reset_token)
        db.commit()

        # MVP: Log reset code to console (replace with email service in production)
        print(f"[AUTH] Password reset code for {user.email}: {reset_code}")
        print(f"[AUTH] Code expires at: {expires_at}")

    # Always return success (don't reveal if email exists)
    return MessageResponse(message="If the email exists, a reset code has been sent")


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset Password",
    description="Reset password using 6-digit code"
)
async def reset_password(
    request: PasswordResetConfirm,
    db: Session = Depends(get_db)
) -> MessageResponse:
    """
    Reset password using 6-digit reset code.

    Validation:
    - Reset code must exist, match email, not be expired, and not be used
    - New password must meet strength requirements

    On success:
    - Updates password
    - Marks reset token as used
    - Revokes all refresh tokens (forces re-login on all devices)

    Returns:
        Success message

    Raises:
        HTTPException 400: If reset code is invalid or password is weak
    """
    normalized_email = normalize_email(request.email)

    # Find user
    user = db.query(User).filter(
        User.email == normalized_email,
        User.deleted_at.is_(None)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset code or email"
        )

    # Hash the reset code
    code_hash = hash_token(request.reset_token)

    # Find valid reset token
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.token_hash == code_hash,
        PasswordResetToken.expires_at > datetime.utcnow(),
        PasswordResetToken.used_at.is_(None)
    ).first()

    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset code"
        )

    # Validate new password strength
    is_valid, error_message = validate_password_strength(request.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )

    # Update password
    user.password_hash = hash_password(request.new_password)

    # Mark reset token as used
    reset_token.used_at = datetime.utcnow()

    # Revoke all refresh tokens (force re-login on all devices)
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user.id,
        RefreshToken.revoked_at.is_(None)
    ).update({"revoked_at": datetime.utcnow()})

    db.commit()

    print(f"[AUTH] Password reset successful for user: {user.email}")

    return MessageResponse(message="Password reset successfully. Please login with your new password.")


@router.post(
    "/google-signin",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Google OAuth Sign-In",
    description="Authenticate with Google ID token"
)
async def google_signin(
    request: GoogleSignInRequest,
    db: Session = Depends(get_db)
) -> LoginResponse:
    """
    Authenticate or create user via Google OAuth.

    Phase 1 implementation:
    - Verifies Google ID token (TODO: Add google-auth library verification)
    - Creates user if doesn't exist (upsert flow)
    - Returns same response as email/password login

    Returns:
        Access token, refresh token, and user data

    Raises:
        HTTPException 401: If Google token is invalid
        HTTPException 500: If Google verification fails
    """
    try:
        # TODO: Implement Google token verification with google-auth library
        # For MVP, this is a placeholder that would need:
        # from google.oauth2 import id_token
        # from google.auth.transport import requests
        #
        # idinfo = id_token.verify_oauth2_token(
        #     request.id_token,
        #     requests.Request(),
        #     os.getenv("GOOGLE_OAUTH_CLIENT_ID")
        # )
        #
        # email = idinfo['email']
        # name = idinfo.get('name', email.split('@')[0])
        # google_user_id = idinfo['sub']

        # PLACEHOLDER for MVP (remove in production)
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth integration pending google-auth library setup. See Task 11 implementation notes."
        )

        # Once Google verification is implemented, continue with:
        # normalized_email = normalize_email(email)
        #
        # # Find or create user
        # user = db.query(User).filter(User.email == normalized_email).first()
        #
        # if not user:
        #     # Create new user via OAuth
        #     user = User(
        #         email=normalized_email,
        #         name=name,
        #         google_oauth_id=google_user_id,
        #         oauth_provider='google',
        #         subscription_type='free'
        #     )
        #     db.add(user)
        # else:
        #     # Link Google OAuth to existing account
        #     user.google_oauth_id = google_user_id
        #     user.oauth_provider = 'google'
        #
        # db.commit()
        # db.refresh(user)
        #
        # # Generate tokens (same as email/password login)
        # access_token = create_access_token(...)
        # refresh_token_str, token_id = create_refresh_token(...)
        # ...

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google authentication failed: {str(e)}"
        )
