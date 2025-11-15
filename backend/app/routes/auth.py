"""
Authentication routes for signup, login, logout, password reset, and OAuth.
Implements JWT-based authentication with bcrypt password hashing.
"""
from datetime import datetime, timedelta
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User, Session as SessionModel, PasswordReset
from app.schemas import (
    SignupRequest, LoginRequest, TokenResponse, UserResponse,
    PasswordResetRequest, PasswordResetConfirm, GoogleCallbackRequest,
    MessageResponse
)
from app.security import (
    hash_password, verify_password, validate_password_strength,
    create_access_token, get_current_user, hash_token, blacklist_token,
    generate_reset_token
)
from app.oauth import get_google_authorization_url, exchange_google_code_for_token

router = APIRouter()


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """
    Register a new user with email and password.

    Args:
        request: Signup request with email, name, and password
        db: Database session

    Returns:
        TokenResponse with user info and JWT token

    Raises:
        HTTPException: 409 if email already exists, 400 if password is weak
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # Validate password strength
    is_valid, error_message = validate_password_strength(request.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )

    # Hash password
    password_hash = hash_password(request.password)

    # Create user
    user = User(
        email=request.email,
        name=request.name,
        password_hash=password_hash,
        subscription_tier="free"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create JWT token
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})

    # Create session
    token_hash_value = hash_token(access_token)
    session = SessionModel(
        user_id=user.id,
        token_hash=token_hash_value,
        expires_at=datetime.utcnow() + timedelta(days=settings.SESSION_EXPIRE_DAYS)
    )
    db.add(session)
    db.commit()

    return TokenResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        token_type="bearer"
    )


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user with email and password.

    Args:
        request: Login request with email and password
        db: Database session

    Returns:
        TokenResponse with user info and JWT token

    Raises:
        HTTPException: 401 if credentials are invalid
    """
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()

    # Verify password (use constant-time comparison to prevent timing attacks)
    if not user or not user.password_hash or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Invalidate previous sessions for this user (one session per user)
    db.query(SessionModel).filter(SessionModel.user_id == user.id).delete()

    # Create JWT token
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})

    # Create new session
    token_hash_value = hash_token(access_token)
    session = SessionModel(
        user_id=user.id,
        token_hash=token_hash_value,
        expires_at=datetime.utcnow() + timedelta(days=settings.SESSION_EXPIRE_DAYS)
    )
    db.add(session)
    db.commit()

    return TokenResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        token_type="bearer"
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.

    Args:
        current_user: Current user from JWT token

    Returns:
        UserResponse with current user info (password_hash excluded)
    """
    return UserResponse.model_validate(current_user)


@router.post("/logout", response_model=MessageResponse)
def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Log out current user and invalidate session.

    Args:
        current_user: Current user from JWT token
        db: Database session

    Returns:
        MessageResponse confirming logout
    """
    # Delete session from database
    db.query(SessionModel).filter(SessionModel.user_id == current_user.id).delete()
    db.commit()

    # Note: We can't access the raw token here easily, so we rely on session deletion
    # The token will be considered invalid because the session is gone

    return MessageResponse(message="Logged out successfully")


@router.post("/request-reset", response_model=MessageResponse)
def request_password_reset(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """
    Request a password reset token.
    Always returns success to prevent user enumeration.

    Args:
        request: Password reset request with email
        db: Database session

    Returns:
        MessageResponse with instructions (same message regardless of user existence)
    """
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()

    if user:
        # Generate secure reset token
        reset_token = generate_reset_token()

        # Create password reset record
        password_reset = PasswordReset(
            user_id=user.id,
            token=reset_token,
            expires_at=datetime.utcnow() + timedelta(hours=settings.RESET_TOKEN_EXPIRE_HOURS)
        )
        db.add(password_reset)
        db.commit()

        # In production: Send email with reset link
        # For now (dev/test): Return token in response or log it
        # TODO: Implement email sending in production

    # Always return the same message to prevent user enumeration
    return MessageResponse(message="If an account with that email exists, a password reset link has been sent")


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(request: PasswordResetConfirm, db: Session = Depends(get_db)):
    """
    Complete password reset with reset token.

    Args:
        request: Password reset confirmation with token and new password
        db: Database session

    Returns:
        MessageResponse confirming password reset

    Raises:
        HTTPException: 400 if token is invalid, expired, or already used
    """
    # Find password reset record
    password_reset = db.query(PasswordReset).filter(
        PasswordReset.token == request.reset_token
    ).first()

    if not password_reset:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Check if token is expired
    if password_reset.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )

    # Check if token has already been used
    if password_reset.used_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has already been used"
        )

    # Validate new password strength
    is_valid, error_message = validate_password_strength(request.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )

    # Hash new password
    new_password_hash = hash_password(request.new_password)

    # Update user password
    user = db.query(User).filter(User.id == password_reset.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )

    user.password_hash = new_password_hash
    password_reset.used_at = datetime.utcnow()
    db.commit()

    # Invalidate all sessions for this user
    db.query(SessionModel).filter(SessionModel.user_id == user.id).delete()
    db.commit()

    return MessageResponse(message="Password reset successful")


@router.get("/google/login-url")
def get_google_login_url():
    """
    Get Google OAuth authorization URL.

    Returns:
        Dictionary with authorization URL
    """
    authorization_url = get_google_authorization_url(settings.GOOGLE_REDIRECT_URI)
    return {"authorization_url": authorization_url}


@router.post("/google/callback", response_model=TokenResponse)
async def google_callback(request: GoogleCallbackRequest, db: Session = Depends(get_db)):
    """
    Handle Google OAuth callback and create/login user.

    Args:
        request: Google callback request with authorization code
        db: Database session

    Returns:
        TokenResponse with user info and JWT token

    Raises:
        HTTPException: 401 if code exchange fails
    """
    # Exchange code for token and user info
    google_data = await exchange_google_code_for_token(request.code, settings.GOOGLE_REDIRECT_URI)
    userinfo = google_data['userinfo']

    # Extract user information from Google
    google_sub = userinfo.get('sub')
    email = userinfo.get('email')
    name = userinfo.get('name', email.split('@')[0])

    if not google_sub or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to retrieve user information from Google"
        )

    # Check if user exists by google_sub
    user = db.query(User).filter(User.google_sub == google_sub).first()

    if not user:
        # Check if user exists by email
        user = db.query(User).filter(User.email == email).first()

        if user:
            # Link Google account to existing user
            user.google_sub = google_sub
            db.commit()
        else:
            # Create new user
            user = User(
                email=email,
                name=name,
                google_sub=google_sub,
                subscription_tier="free"
            )
            db.add(user)
            db.commit()
            db.refresh(user)

    # Invalidate previous sessions for this user (one session per user)
    db.query(SessionModel).filter(SessionModel.user_id == user.id).delete()

    # Create JWT token
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})

    # Create new session
    token_hash_value = hash_token(access_token)
    session = SessionModel(
        user_id=user.id,
        token_hash=token_hash_value,
        expires_at=datetime.utcnow() + timedelta(days=settings.SESSION_EXPIRE_DAYS)
    )
    db.add(session)
    db.commit()

    return TokenResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        token_type="bearer"
    )
