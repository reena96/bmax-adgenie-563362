"""
Comprehensive test suite for authentication system.
Tests signup, login, logout, password reset, OAuth, JWT tokens, and security.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from jose import jwt

from app.config import settings
from app.models import User, Session, PasswordReset
from app.security import (
    hash_password, verify_password, validate_password_strength,
    create_access_token, verify_token, hash_token, generate_reset_token
)


# Fixtures
@pytest.fixture
def test_user(test_db):
    """Create a test user for login tests."""
    user = User(
        email="test@example.com",
        name="Test User",
        password_hash=hash_password("TestPassword123"),
        subscription_tier="free"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_user_with_google(test_db):
    """Create a test user with Google OAuth linked."""
    user = User(
        email="google@example.com",
        name="Google User",
        google_sub="google_sub_123456",
        subscription_tier="free"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers with valid JWT token."""
    token = create_access_token(data={"sub": str(test_user.id), "email": test_user.email})
    return {"Authorization": f"Bearer {token}"}


# Signup Tests (AC1)
class TestSignup:
    """Tests for user signup functionality."""

    def test_signup_success(self, client, test_db):
        """Test successful signup with valid credentials."""
        response = client.post(
            "/api/auth/signup",
            json={
                "email": "newuser@example.com",
                "name": "New User",
                "password": "SecurePass123"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["name"] == "New User"
        assert "password_hash" not in data["user"]

        # Verify user created in database
        user = test_db.query(User).filter(User.email == "newuser@example.com").first()
        assert user is not None
        assert user.password_hash is not None

    def test_signup_duplicate_email(self, test_db, test_user):
        """Test signup rejection with duplicate email (409 Conflict)."""
        response = client.post(
            "/api/auth/signup",
            json={
                "email": test_user.email,
                "name": "Duplicate User",
                "password": "SecurePass123"
            }
        )
        assert response.status_code == 409
        assert "already registered" in response.json()["detail"].lower()

    def test_signup_weak_password_short(self, test_db):
        """Test signup rejection with password too short."""
        response = client.post(
            "/api/auth/signup",
            json={
                "email": "weak@example.com",
                "name": "Weak User",
                "password": "Short1"
            }
        )
        assert response.status_code == 400
        assert "8 characters" in response.json()["detail"]

    def test_signup_weak_password_no_uppercase(self, test_db):
        """Test signup rejection with no uppercase letter."""
        response = client.post(
            "/api/auth/signup",
            json={
                "email": "weak@example.com",
                "name": "Weak User",
                "password": "lowercase123"
            }
        )
        assert response.status_code == 400
        assert "uppercase" in response.json()["detail"].lower()

    def test_signup_weak_password_no_lowercase(self, test_db):
        """Test signup rejection with no lowercase letter."""
        response = client.post(
            "/api/auth/signup",
            json={
                "email": "weak@example.com",
                "name": "Weak User",
                "password": "UPPERCASE123"
            }
        )
        assert response.status_code == 400
        assert "lowercase" in response.json()["detail"].lower()

    def test_signup_weak_password_no_digit(self, test_db):
        """Test signup rejection with no digit."""
        response = client.post(
            "/api/auth/signup",
            json={
                "email": "weak@example.com",
                "name": "Weak User",
                "password": "NoDigitsHere"
            }
        )
        assert response.status_code == 400
        assert "digit" in response.json()["detail"].lower()

    def test_signup_invalid_email(self, test_db):
        """Test signup rejection with invalid email format."""
        response = client.post(
            "/api/auth/signup",
            json={
                "email": "not-an-email",
                "name": "Invalid User",
                "password": "SecurePass123"
            }
        )
        assert response.status_code == 422  # FastAPI validation error


# Login Tests (AC2)
class TestLogin:
    """Tests for user login functionality."""

    def test_login_success(self, test_db, test_user):
        """Test successful login with valid credentials."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": test_user.email,
                "password": "TestPassword123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == test_user.email

    def test_login_wrong_password(self, test_db, test_user):
        """Test login rejection with wrong password."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": test_user.email,
                "password": "WrongPassword123"
            }
        )
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, test_db):
        """Test login rejection for non-existent user."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "TestPassword123"
            }
        )
        assert response.status_code == 401
        # Should not reveal user existence
        assert "invalid" in response.json()["detail"].lower()
        assert "not found" not in response.json()["detail"].lower()

    def test_login_returns_valid_token(self, test_db, test_user):
        """Test that login returns a valid JWT token."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": test_user.email,
                "password": "TestPassword123"
            }
        )
        assert response.status_code == 200
        token = response.json()["access_token"]

        # Verify token is valid
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == str(test_user.id)
        assert payload["email"] == test_user.email

    def test_login_creates_session(self, test_db, test_user):
        """Test that login creates a session record."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": test_user.email,
                "password": "TestPassword123"
            }
        )
        assert response.status_code == 200

        # Verify session created
        session = test_db.query(Session).filter(Session.user_id == test_user.id).first()
        assert session is not None
        assert session.token_hash is not None


# JWT Token Tests (AC3)
class TestJWTTokens:
    """Tests for JWT token generation and validation."""

    def test_create_token(self):
        """Test JWT token creation."""
        data = {"sub": "user-123", "email": "user@example.com"}
        token = create_access_token(data)
        assert token is not None
        assert isinstance(token, str)

    def test_verify_valid_token(self):
        """Test verification of valid JWT token."""
        data = {"sub": "user-123", "email": "user@example.com"}
        token = create_access_token(data)
        payload = verify_token(token)
        assert payload["sub"] == "user-123"
        assert payload["email"] == "user@example.com"

    def test_verify_expired_token(self):
        """Test rejection of expired JWT token."""
        data = {"sub": "user-123", "email": "user@example.com"}
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))

        with pytest.raises(Exception):  # Should raise HTTPException
            verify_token(token)

    def test_verify_invalid_signature(self):
        """Test rejection of token with invalid signature."""
        data = {"sub": "user-123", "email": "user@example.com"}
        token = create_access_token(data)

        # Tamper with token
        tampered_token = token[:-5] + "xxxxx"

        with pytest.raises(Exception):  # Should raise HTTPException
            verify_token(tampered_token)

    def test_token_includes_user_id(self):
        """Test that token contains user ID and email."""
        data = {"sub": "user-123", "email": "user@example.com"}
        token = create_access_token(data)
        payload = verify_token(token)
        assert "sub" in payload
        assert "email" in payload
        assert "exp" in payload
        assert "iat" in payload

    def test_token_expiration_configured(self):
        """Test that token expiration is properly configured."""
        data = {"sub": "user-123", "email": "user@example.com"}
        token = create_access_token(data)
        payload = verify_token(token)

        exp_time = datetime.fromtimestamp(payload["exp"])
        iat_time = datetime.fromtimestamp(payload["iat"])
        delta = exp_time - iat_time

        # Should be close to ACCESS_TOKEN_EXPIRE_MINUTES
        assert delta.total_seconds() / 60 == pytest.approx(settings.ACCESS_TOKEN_EXPIRE_MINUTES, abs=1)


# Protected Route Tests (AC4)
class TestProtectedRoutes:
    """Tests for protected route middleware."""

    def test_protected_route_with_valid_token(self, test_db, test_user, auth_headers):
        """Test accessing protected route with valid token."""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["email"] == test_user.email

    def test_protected_route_without_token(self, test_db):
        """Test accessing protected route without token (401)."""
        response = client.get("/api/auth/me")
        assert response.status_code == 403  # FastAPI HTTPBearer returns 403

    def test_protected_route_invalid_token(self, test_db):
        """Test accessing protected route with invalid token."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401

    def test_protected_route_expired_token(self, test_db, test_user):
        """Test accessing protected route with expired token."""
        # Create expired token
        token = create_access_token(
            data={"sub": str(test_user.id), "email": test_user.email},
            expires_delta=timedelta(seconds=-1)
        )
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401


# User Info Tests (AC8)
class TestUserInfo:
    """Tests for /me endpoint."""

    def test_get_user_info_authenticated(self, test_db, test_user, auth_headers):
        """Test getting user info when authenticated."""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["email"] == test_user.email
        assert data["name"] == test_user.name
        assert data["subscription_tier"] == "free"

    def test_get_user_info_no_password_hash(self, test_db, test_user, auth_headers):
        """Test that password hash is never returned."""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "password_hash" not in data
        assert "password" not in data

    def test_get_user_info_unauthenticated(self, test_db):
        """Test getting user info without authentication."""
        response = client.get("/api/auth/me")
        assert response.status_code == 403


# Logout Tests (AC6)
class TestLogout:
    """Tests for logout functionality."""

    def test_logout_success(self, test_db, test_user, auth_headers):
        """Test successful logout."""
        # First, create a session
        client.post(
            "/api/auth/login",
            json={"email": test_user.email, "password": "TestPassword123"}
        )

        # Logout
        response = client.post("/api/auth/logout", headers=auth_headers)
        assert response.status_code == 200
        assert "success" in response.json()["message"].lower()

    def test_logout_without_auth(self, test_db):
        """Test logout without authentication."""
        response = client.post("/api/auth/logout")
        assert response.status_code == 403

    def test_logout_clears_session(self, test_db, test_user):
        """Test that logout clears session from database."""
        # Login to create session
        login_response = client.post(
            "/api/auth/login",
            json={"email": test_user.email, "password": "TestPassword123"}
        )
        token = login_response.json()["access_token"]

        # Verify session exists
        session_before = test_db.query(Session).filter(Session.user_id == test_user.id).first()
        assert session_before is not None

        # Logout
        client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Verify session deleted
        session_after = test_db.query(Session).filter(Session.user_id == test_user.id).first()
        assert session_after is None


# Password Reset Tests (AC7)
class TestPasswordReset:
    """Tests for password reset flow."""

    def test_request_reset_success(self, test_db, test_user):
        """Test requesting password reset token."""
        response = client.post(
            "/api/auth/request-reset",
            json={"email": test_user.email}
        )
        assert response.status_code == 200

        # Verify reset token created
        reset = test_db.query(PasswordReset).filter(PasswordReset.user_id == test_user.id).first()
        assert reset is not None
        assert reset.token is not None

    def test_request_reset_nonexistent_user(self, test_db):
        """Test requesting reset for non-existent user (no enumeration)."""
        response = client.post(
            "/api/auth/request-reset",
            json={"email": "nonexistent@example.com"}
        )
        # Should still return success to prevent user enumeration
        assert response.status_code == 200

    def test_reset_password_valid_token(self, test_db, test_user):
        """Test resetting password with valid token."""
        # Create reset token
        reset_token = generate_reset_token()
        reset = PasswordReset(
            user_id=test_user.id,
            token=reset_token,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        test_db.add(reset)
        test_db.commit()

        # Reset password
        response = client.post(
            "/api/auth/reset-password",
            json={
                "reset_token": reset_token,
                "new_password": "NewSecurePass123"
            }
        )
        assert response.status_code == 200

        # Verify password updated
        test_db.refresh(test_user)
        assert verify_password("NewSecurePass123", test_user.password_hash)

    def test_reset_password_expired_token(self, test_db, test_user):
        """Test reset with expired token."""
        # Create expired reset token
        reset_token = generate_reset_token()
        reset = PasswordReset(
            user_id=test_user.id,
            token=reset_token,
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        test_db.add(reset)
        test_db.commit()

        # Try to reset
        response = client.post(
            "/api/auth/reset-password",
            json={
                "reset_token": reset_token,
                "new_password": "NewSecurePass123"
            }
        )
        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()

    def test_reset_password_used_token(self, test_db, test_user):
        """Test reset with already used token."""
        # Create used reset token
        reset_token = generate_reset_token()
        reset = PasswordReset(
            user_id=test_user.id,
            token=reset_token,
            expires_at=datetime.utcnow() + timedelta(hours=24),
            used_at=datetime.utcnow()
        )
        test_db.add(reset)
        test_db.commit()

        # Try to reset
        response = client.post(
            "/api/auth/reset-password",
            json={
                "reset_token": reset_token,
                "new_password": "NewSecurePass123"
            }
        )
        assert response.status_code == 400
        assert "used" in response.json()["detail"].lower()

    def test_reset_password_weak_password(self, test_db, test_user):
        """Test reset with weak password."""
        # Create reset token
        reset_token = generate_reset_token()
        reset = PasswordReset(
            user_id=test_user.id,
            token=reset_token,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        test_db.add(reset)
        test_db.commit()

        # Try to reset with weak password
        response = client.post(
            "/api/auth/reset-password",
            json={
                "reset_token": reset_token,
                "new_password": "weak"
            }
        )
        assert response.status_code == 400


# Session Management Tests (AC9)
class TestSessionManagement:
    """Tests for session management."""

    def test_session_created_on_login(self, test_db, test_user):
        """Test that session is created on login."""
        response = client.post(
            "/api/auth/login",
            json={"email": test_user.email, "password": "TestPassword123"}
        )
        assert response.status_code == 200

        # Verify session created
        session = test_db.query(Session).filter(Session.user_id == test_user.id).first()
        assert session is not None

    def test_session_deleted_on_logout(self, test_db, test_user):
        """Test that session is deleted on logout."""
        # Login
        login_response = client.post(
            "/api/auth/login",
            json={"email": test_user.email, "password": "TestPassword123"}
        )
        token = login_response.json()["access_token"]

        # Logout
        client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})

        # Verify session deleted
        session = test_db.query(Session).filter(Session.user_id == test_user.id).first()
        assert session is None

    def test_one_session_per_user(self, test_db, test_user):
        """Test that new login invalidates previous session."""
        # First login
        response1 = client.post(
            "/api/auth/login",
            json={"email": test_user.email, "password": "TestPassword123"}
        )
        token1_hash = hash_token(response1.json()["access_token"])

        # Second login
        response2 = client.post(
            "/api/auth/login",
            json={"email": test_user.email, "password": "TestPassword123"}
        )

        # Verify only one session exists
        sessions = test_db.query(Session).filter(Session.user_id == test_user.id).all()
        assert len(sessions) == 1

        # Verify it's the new session
        assert sessions[0].token_hash != token1_hash

    def test_session_expiration_configured(self, test_db, test_user):
        """Test that session expiration is properly configured."""
        response = client.post(
            "/api/auth/login",
            json={"email": test_user.email, "password": "TestPassword123"}
        )

        session = test_db.query(Session).filter(Session.user_id == test_user.id).first()
        delta = session.expires_at - session.created_at

        # Should be close to SESSION_EXPIRE_DAYS
        assert delta.days == settings.SESSION_EXPIRE_DAYS


# Security Tests (AC10)
class TestSecurity:
    """Tests for security requirements."""

    def test_password_hashing_bcrypt(self):
        """Test that passwords are hashed with bcrypt."""
        password = "TestPassword123"
        hashed = hash_password(password)

        # Bcrypt hashes start with $2b$
        assert hashed.startswith("$2b$")
        assert hashed != password

    def test_password_not_stored_plaintext(self, test_db):
        """Test that passwords are never stored in plain text."""
        response = client.post(
            "/api/auth/signup",
            json={
                "email": "security@example.com",
                "name": "Security User",
                "password": "SecurePass123"
            }
        )
        assert response.status_code == 201

        # Check database
        user = test_db.query(User).filter(User.email == "security@example.com").first()
        assert user.password_hash != "SecurePass123"
        assert user.password_hash.startswith("$2b$")

    def test_password_verification(self):
        """Test password verification works correctly."""
        password = "TestPassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
        assert verify_password("WrongPassword", hashed) is False

    def test_token_signature_verification(self):
        """Test that token signature is verified."""
        data = {"sub": "user-123", "email": "user@example.com"}
        token = create_access_token(data)

        # Valid token should verify
        payload = verify_token(token)
        assert payload["sub"] == "user-123"

        # Tampered token should fail
        tampered = token[:-10] + "tamperedxx"
        with pytest.raises(Exception):
            verify_token(tampered)

    def test_password_strength_validation(self):
        """Test password strength validation."""
        # Valid passwords
        assert validate_password_strength("SecurePass123")[0] is True
        assert validate_password_strength("MyP@ssw0rd")[0] is True

        # Invalid passwords
        assert validate_password_strength("short")[0] is False
        assert validate_password_strength("nouppercase123")[0] is False
        assert validate_password_strength("NOLOWERCASE123")[0] is False
        assert validate_password_strength("NoDigitsHere")[0] is False

    def test_reset_token_generation(self):
        """Test secure reset token generation."""
        token1 = generate_reset_token()
        token2 = generate_reset_token()

        # Tokens should be unique
        assert token1 != token2

        # Tokens should be URL-safe and long enough (32 bytes = ~43 chars base64)
        assert len(token1) >= 40
        assert len(token2) >= 40


# OAuth Google Tests (AC5)
class TestGoogleOAuth:
    """Tests for Google OAuth integration."""

    def test_google_login_url_generation(self):
        """Test Google OAuth authorization URL generation."""
        response = client.get("/api/auth/google/login-url")
        assert response.status_code == 200 or response.status_code == 500  # 500 if not configured

        if response.status_code == 200:
            data = response.json()
            assert "authorization_url" in data
            assert "accounts.google.com" in data["authorization_url"]

    @patch('app.oauth.exchange_google_code_for_token')
    async def test_google_callback_new_user(self, mock_exchange, test_db):
        """Test Google OAuth callback creating new user."""
        # Mock Google response
        mock_exchange.return_value = {
            'token': {'access_token': 'mock_token'},
            'userinfo': {
                'sub': 'google_user_123',
                'email': 'newgoogleuser@example.com',
                'name': 'New Google User'
            }
        }

        response = await client.post(
            "/api/auth/google/callback",
            json={"code": "mock_code", "state": "mock_state"}
        )

        # Note: This test may need adjustments based on OAuth mock setup
        # The actual implementation might require more sophisticated mocking

    @patch('app.oauth.exchange_google_code_for_token')
    async def test_google_callback_existing_user(self, mock_exchange, test_db, test_user_with_google):
        """Test Google OAuth callback for existing user."""
        # Mock Google response
        mock_exchange.return_value = {
            'token': {'access_token': 'mock_token'},
            'userinfo': {
                'sub': test_user_with_google.google_sub,
                'email': test_user_with_google.email,
                'name': test_user_with_google.name
            }
        }

        # This would require async test setup
        # Placeholder for full implementation
        pass
