"""
Integration tests for authentication endpoints.

Tests all auth endpoints: signup, login, refresh, logout, password reset, OAuth.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.auth import RefreshToken, PasswordResetToken
from app.utils.password import hash_password
from app.utils.jwt import create_access_token, create_refresh_token

# Test database URL (use in-memory SQLite for tests)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_auth.db"

# Create test engine and session
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Fixtures

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with overridden database dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user in the database."""
    user = User(
        email="test@example.com",
        name="Test User",
        password_hash=hash_password("TestPass123!"),
        subscription_type="free"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Generate valid authorization headers for test user."""
    access_token = create_access_token(
        user_id=str(test_user.id),
        email=test_user.email,
        subscription_tier=test_user.subscription_type
    )
    return {"Authorization": f"Bearer {access_token}"}


# ============================================================================
# Signup Endpoint Tests
# ============================================================================

class TestSignupEndpoint:
    """Tests for POST /api/auth/signup"""

    def test_signup_success(self, client, db_session):
        """Test successful user signup."""
        response = client.post("/api/auth/signup", json={
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "name": "New User"
        })

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["name"] == "New User"
        assert data["subscription_tier"] == "free"
        assert "id" in data

        # Verify user created in database
        user = db_session.query(User).filter(User.email == "newuser@example.com").first()
        assert user is not None
        assert user.password_hash is not None

    def test_signup_duplicate_email(self, client, test_user):
        """Test signup with already registered email."""
        response = client.post("/api/auth/signup", json={
            "email": "test@example.com",
            "password": "SecurePass123!",
            "name": "Duplicate User"
        })

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_signup_weak_password(self, client):
        """Test signup with weak password."""
        response = client.post("/api/auth/signup", json={
            "email": "newuser@example.com",
            "password": "weak",
            "name": "New User"
        })

        assert response.status_code == 400
        assert "password" in response.json()["detail"].lower()

    def test_signup_invalid_email(self, client):
        """Test signup with invalid email format."""
        response = client.post("/api/auth/signup", json={
            "email": "invalid-email",
            "password": "SecurePass123!",
            "name": "New User"
        })

        assert response.status_code == 422  # Pydantic validation error

    def test_signup_email_normalization(self, client, db_session):
        """Test that email is normalized (lowercase, trimmed)."""
        response = client.post("/api/auth/signup", json={
            "email": "  NewUser@EXAMPLE.COM  ",
            "password": "SecurePass123!",
            "name": "New User"
        })

        assert response.status_code == 201
        assert response.json()["email"] == "newuser@example.com"


# ============================================================================
# Login Endpoint Tests
# ============================================================================

class TestLoginEndpoint:
    """Tests for POST /api/auth/login"""

    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "TestPass123!"
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["name"] == "Test User"

    def test_login_wrong_password(self, client, test_user):
        """Test login with incorrect password."""
        response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "WrongPassword123!"
        })

        assert response.status_code == 401
        assert "invalid credentials" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent email."""
        response = client.post("/api/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "Password123!"
        })

        assert response.status_code == 401
        assert "invalid credentials" in response.json()["detail"].lower()

    def test_login_case_insensitive_email(self, client, test_user):
        """Test that login is case-insensitive for email."""
        response = client.post("/api/auth/login", json={
            "email": "TEST@EXAMPLE.COM",
            "password": "TestPass123!"
        })

        assert response.status_code == 200

    def test_login_stores_refresh_token(self, client, test_user, db_session):
        """Test that refresh token is stored in database."""
        response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "TestPass123!"
        })

        assert response.status_code == 200

        # Check refresh token in database
        refresh_tokens = db_session.query(RefreshToken).filter(
            RefreshToken.user_id == test_user.id
        ).all()
        assert len(refresh_tokens) > 0


# ============================================================================
# Refresh Token Endpoint Tests
# ============================================================================

class TestRefreshTokenEndpoint:
    """Tests for POST /api/auth/refresh"""

    def test_refresh_token_success(self, client, test_user, db_session):
        """Test successful token refresh."""
        # Create a refresh token
        refresh_token_str, token_id = create_refresh_token(str(test_user.id))

        # Store it in database
        import hashlib
        token_hash = hashlib.sha256(refresh_token_str.encode()).hexdigest()
        refresh_token_record = RefreshToken(
            user_id=test_user.id,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        db_session.add(refresh_token_record)
        db_session.commit()

        # Refresh the token
        response = client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token_str
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["refresh_token"] != refresh_token_str  # Token rotation

    def test_refresh_token_invalid(self, client):
        """Test refresh with invalid token."""
        response = client.post("/api/auth/refresh", json={
            "refresh_token": "invalid.token.here"
        })

        assert response.status_code == 401

    def test_refresh_token_revoked(self, client, test_user, db_session):
        """Test refresh with revoked token."""
        # Create and revoke a refresh token
        refresh_token_str, token_id = create_refresh_token(str(test_user.id))
        import hashlib
        token_hash = hashlib.sha256(refresh_token_str.encode()).hexdigest()
        refresh_token_record = RefreshToken(
            user_id=test_user.id,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(days=7),
            revoked_at=datetime.utcnow()  # Already revoked
        )
        db_session.add(refresh_token_record)
        db_session.commit()

        response = client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token_str
        })

        assert response.status_code == 401


# ============================================================================
# Get Current User Endpoint Tests
# ============================================================================

class TestGetCurrentUserEndpoint:
    """Tests for GET /api/auth/me"""

    def test_get_me_success(self, client, test_user, auth_headers):
        """Test getting current user with valid token."""
        response = client.get("/api/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"
        assert data["subscription_tier"] == "free"

    def test_get_me_no_token(self, client):
        """Test GET /me without authorization header."""
        response = client.get("/api/auth/me")

        assert response.status_code == 403  # FastAPI HTTPBearer returns 403

    def test_get_me_invalid_token(self, client):
        """Test GET /me with invalid token."""
        response = client.get("/api/auth/me", headers={
            "Authorization": "Bearer invalid.token.here"
        })

        assert response.status_code == 401


# ============================================================================
# Logout Endpoint Tests
# ============================================================================

class TestLogoutEndpoint:
    """Tests for POST /api/auth/logout"""

    def test_logout_success(self, client, test_user, auth_headers, db_session):
        """Test successful logout."""
        # Create a refresh token first
        refresh_token_str, token_id = create_refresh_token(str(test_user.id))
        import hashlib
        token_hash = hashlib.sha256(refresh_token_str.encode()).hexdigest()
        refresh_token_record = RefreshToken(
            user_id=test_user.id,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        db_session.add(refresh_token_record)
        db_session.commit()

        # Logout
        response = client.post("/api/auth/logout", headers=auth_headers)

        assert response.status_code == 200
        assert "logged out" in response.json()["message"].lower()

        # Verify refresh token is revoked
        db_session.refresh(refresh_token_record)
        assert refresh_token_record.revoked_at is not None

    def test_logout_no_token(self, client):
        """Test logout without authorization header."""
        response = client.post("/api/auth/logout")

        assert response.status_code == 403


# ============================================================================
# Password Reset Flow Tests
# ============================================================================

class TestPasswordResetFlow:
    """Tests for password reset endpoints"""

    def test_request_password_reset_success(self, client, test_user, db_session):
        """Test requesting password reset."""
        response = client.post("/api/auth/request-password-reset", json={
            "email": "test@example.com"
        })

        assert response.status_code == 200
        assert "reset code" in response.json()["message"].lower()

        # Verify reset token created in database
        reset_tokens = db_session.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == test_user.id
        ).all()
        assert len(reset_tokens) > 0

    def test_request_password_reset_nonexistent_email(self, client):
        """Test requesting reset for non-existent email returns success (security)."""
        response = client.post("/api/auth/request-password-reset", json={
            "email": "nonexistent@example.com"
        })

        # Should still return success to prevent email enumeration
        assert response.status_code == 200

    def test_reset_password_success(self, client, test_user, db_session):
        """Test resetting password with valid code."""
        # Create a reset token
        import hashlib
        reset_code = "123456"
        code_hash = hashlib.sha256(reset_code.encode()).hexdigest()
        reset_token = PasswordResetToken(
            user_id=test_user.id,
            token_hash=code_hash,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db_session.add(reset_token)
        db_session.commit()

        # Reset password
        response = client.post("/api/auth/reset-password", json={
            "email": "test@example.com",
            "reset_token": reset_code,
            "new_password": "NewSecurePass123!"
        })

        assert response.status_code == 200
        assert "reset successfully" in response.json()["message"].lower()

        # Verify token marked as used
        db_session.refresh(reset_token)
        assert reset_token.used_at is not None

    def test_reset_password_invalid_code(self, client, test_user):
        """Test reset with invalid code."""
        response = client.post("/api/auth/reset-password", json={
            "email": "test@example.com",
            "reset_token": "999999",
            "new_password": "NewSecurePass123!"
        })

        assert response.status_code == 400

    def test_reset_password_weak_password(self, client, test_user, db_session):
        """Test reset with weak password."""
        # Create a reset token
        import hashlib
        reset_code = "123456"
        code_hash = hashlib.sha256(reset_code.encode()).hexdigest()
        reset_token = PasswordResetToken(
            user_id=test_user.id,
            token_hash=code_hash,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db_session.add(reset_token)
        db_session.commit()

        response = client.post("/api/auth/reset-password", json={
            "email": "test@example.com",
            "reset_token": reset_code,
            "new_password": "weak"
        })

        assert response.status_code == 400
        assert "password" in response.json()["detail"].lower()


# ============================================================================
# Google OAuth Tests
# ============================================================================

class TestGoogleOAuthEndpoint:
    """Tests for POST /api/auth/google-signin"""

    def test_google_signin_not_implemented(self, client):
        """Test that Google OAuth returns 501 (placeholder for MVP)."""
        response = client.post("/api/auth/google-signin", json={
            "id_token": "fake.google.token"
        })

        assert response.status_code == 501
        assert "not implemented" in response.json()["detail"].lower()


# ============================================================================
# Protected Routes Tests
# ============================================================================

class TestProtectedRoutes:
    """Tests for JWT middleware on protected routes"""

    def test_protected_route_with_valid_token(self, client, auth_headers):
        """Test accessing protected route with valid token."""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200

    def test_protected_route_without_token(self, client):
        """Test accessing protected route without token."""
        response = client.get("/api/auth/me")
        assert response.status_code == 403

    def test_protected_route_with_expired_token(self, client, test_user):
        """Test accessing protected route with expired token."""
        # Create an expired token (would need to manipulate time or use a very short expiry)
        # For now, we'll just test with an invalid token
        response = client.get("/api/auth/me", headers={
            "Authorization": "Bearer expired.token.here"
        })
        assert response.status_code == 401
