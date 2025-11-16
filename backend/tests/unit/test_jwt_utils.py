"""
Unit tests for JWT token utilities.

Tests token creation, verification, and expiration handling.
"""
import pytest
import time
from datetime import datetime, timedelta
from jose import JWTError

from app.utils.jwt import (
    create_access_token,
    create_refresh_token,
    verify_token,
    verify_access_token,
    verify_refresh_token,
    get_token_expiration,
    is_token_expired
)


class TestAccessTokenCreation:
    """Test access token creation and verification."""

    def test_create_access_token_success(self):
        """Test that access token is created with correct payload."""
        user_id = "test-user-id-123"
        email = "test@example.com"
        subscription_tier = "pro"

        token = create_access_token(user_id, email, subscription_tier)

        assert isinstance(token, str)
        assert len(token) > 0

        # Verify payload
        payload = verify_token(token)
        assert payload["sub"] == user_id
        assert payload["email"] == email
        assert payload["subscription_tier"] == subscription_tier
        assert "iat" in payload
        assert "exp" in payload

    def test_access_token_has_15_minute_expiration(self):
        """Test that access token expires in 15 minutes."""
        token = create_access_token("user-id", "user@example.com", "free")
        payload = verify_token(token)

        issued_at = datetime.fromtimestamp(payload["iat"])
        expires_at = datetime.fromtimestamp(payload["exp"])
        duration = expires_at - issued_at

        # Should be approximately 15 minutes (allow 1 second tolerance)
        assert 899 <= duration.total_seconds() <= 901

    def test_access_token_does_not_have_type_field(self):
        """Test that access tokens don't have type field (only refresh tokens do)."""
        token = create_access_token("user-id", "user@example.com", "free")
        payload = verify_token(token)

        assert "type" not in payload


class TestRefreshTokenCreation:
    """Test refresh token creation and verification."""

    def test_create_refresh_token_success(self):
        """Test that refresh token is created with correct payload."""
        user_id = "test-user-id-123"

        token, jti = create_refresh_token(user_id)

        assert isinstance(token, str)
        assert isinstance(jti, str)
        assert len(token) > 0
        assert len(jti) > 0

        # Verify payload
        payload = verify_token(token)
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"
        assert payload["jti"] == jti
        assert "iat" in payload
        assert "exp" in payload

    def test_refresh_token_has_7_day_expiration(self):
        """Test that refresh token expires in 7 days."""
        token, _ = create_refresh_token("user-id")
        payload = verify_token(token)

        issued_at = datetime.fromtimestamp(payload["iat"])
        expires_at = datetime.fromtimestamp(payload["exp"])
        duration = expires_at - issued_at

        # Should be approximately 7 days (allow 1 second tolerance)
        expected_seconds = 7 * 24 * 60 * 60
        assert expected_seconds - 1 <= duration.total_seconds() <= expected_seconds + 1

    def test_refresh_token_has_unique_jti(self):
        """Test that each refresh token has a unique jti."""
        token1, jti1 = create_refresh_token("user-id")
        token2, jti2 = create_refresh_token("user-id")

        assert jti1 != jti2
        assert token1 != token2


class TestTokenVerification:
    """Test token verification functions."""

    def test_verify_access_token_success(self):
        """Test successful access token verification."""
        token = create_access_token("user-id", "user@example.com", "free")
        payload = verify_access_token(token)

        assert payload["sub"] == "user-id"
        assert payload["email"] == "user@example.com"

    def test_verify_access_token_rejects_refresh_token(self):
        """Test that verify_access_token rejects refresh tokens."""
        token, _ = create_refresh_token("user-id")

        with pytest.raises(JWTError, match="expected access token"):
            verify_access_token(token)

    def test_verify_refresh_token_success(self):
        """Test successful refresh token verification."""
        token, jti = create_refresh_token("user-id")
        payload = verify_refresh_token(token)

        assert payload["sub"] == "user-id"
        assert payload["type"] == "refresh"
        assert payload["jti"] == jti

    def test_verify_refresh_token_rejects_access_token(self):
        """Test that verify_refresh_token rejects access tokens."""
        token = create_access_token("user-id", "user@example.com", "free")

        with pytest.raises(JWTError, match="expected refresh token"):
            verify_refresh_token(token)

    def test_verify_token_with_invalid_token(self):
        """Test that verification fails for invalid tokens."""
        with pytest.raises(JWTError):
            verify_token("invalid.token.string")

    def test_verify_token_with_tampered_token(self):
        """Test that verification fails for tampered tokens."""
        token = create_access_token("user-id", "user@example.com", "free")
        # Tamper with the token
        tampered = token[:-5] + "XXXXX"

        with pytest.raises(JWTError):
            verify_token(tampered)


class TestTokenExpiration:
    """Test token expiration utilities."""

    def test_get_token_expiration_for_access_token(self):
        """Test extracting expiration from access token."""
        token = create_access_token("user-id", "user@example.com", "free")
        exp = get_token_expiration(token)

        assert isinstance(exp, datetime)
        # Should expire in approximately 15 minutes
        time_until_expiry = exp - datetime.utcnow()
        assert 14 * 60 <= time_until_expiry.total_seconds() <= 16 * 60

    def test_get_token_expiration_for_refresh_token(self):
        """Test extracting expiration from refresh token."""
        token, _ = create_refresh_token("user-id")
        exp = get_token_expiration(token)

        assert isinstance(exp, datetime)
        # Should expire in approximately 7 days
        time_until_expiry = exp - datetime.utcnow()
        expected_seconds = 7 * 24 * 60 * 60
        assert expected_seconds - 60 <= time_until_expiry.total_seconds() <= expected_seconds + 60

    def test_get_token_expiration_with_invalid_token(self):
        """Test that invalid tokens return None for expiration."""
        exp = get_token_expiration("invalid.token")
        assert exp is None

    def test_is_token_expired_for_valid_token(self):
        """Test that valid tokens are not expired."""
        token = create_access_token("user-id", "user@example.com", "free")
        assert is_token_expired(token) is False

    def test_is_token_expired_for_invalid_token(self):
        """Test that invalid tokens are considered expired."""
        assert is_token_expired("invalid.token") is True


class TestTokenSecurity:
    """Test security aspects of JWT tokens."""

    def test_tokens_use_hs256_algorithm(self):
        """Test that tokens use HS256 algorithm."""
        import json
        import base64

        token = create_access_token("user-id", "user@example.com", "free")
        # JWT format: header.payload.signature
        header_b64 = token.split('.')[0]
        # Add padding if needed
        header_b64 += '=' * (4 - len(header_b64) % 4)
        header = json.loads(base64.urlsafe_b64decode(header_b64))

        assert header["alg"] == "HS256"
        assert header["typ"] == "JWT"

    def test_different_users_produce_different_tokens(self):
        """Test that tokens for different users are different."""
        token1 = create_access_token("user-1", "user1@example.com", "free")
        token2 = create_access_token("user-2", "user2@example.com", "free")

        assert token1 != token2

    def test_same_user_produces_different_tokens_over_time(self):
        """Test that tokens for same user are different (due to iat)."""
        token1 = create_access_token("user-id", "user@example.com", "free")
        time.sleep(1)  # Wait 1 second for different iat
        token2 = create_access_token("user-id", "user@example.com", "free")

        assert token1 != token2  # Different iat should produce different tokens
