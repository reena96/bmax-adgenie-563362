"""
Unit tests for password utilities.

Tests password hashing, verification, and strength validation.
"""
import pytest
from app.utils.password import (
    hash_password,
    verify_password,
    validate_password_strength,
    get_password_requirements
)


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password_returns_different_hash(self):
        """Test that hashing the same password twice produces different hashes."""
        password = "TestPassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2  # Different salts should produce different hashes
        assert hash1.startswith("$2b$")  # Bcrypt hash identifier
        assert hash2.startswith("$2b$")

    def test_verify_password_with_correct_password(self):
        """Test that verification succeeds with correct password."""
        password = "CorrectPassword123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_with_incorrect_password(self):
        """Test that verification fails with incorrect password."""
        password = "CorrectPassword123!"
        hashed = hash_password(password)

        assert verify_password("WrongPassword123!", hashed) is False

    def test_verify_password_case_sensitive(self):
        """Test that password verification is case-sensitive."""
        password = "CaseSensitive123!"
        hashed = hash_password(password)

        assert verify_password("casesensitive123!", hashed) is False


class TestPasswordStrengthValidation:
    """Test password strength validation."""

    def test_valid_strong_password(self):
        """Test that a strong password passes validation."""
        valid, error = validate_password_strength("StrongPass123!")
        assert valid is True
        assert error == ""

    def test_password_too_short(self):
        """Test that passwords shorter than 8 characters fail."""
        valid, error = validate_password_strength("Short1!")
        assert valid is False
        assert "8 characters" in error

    def test_password_too_long(self):
        """Test that passwords longer than 128 characters fail."""
        long_password = "A1!" + "x" * 130
        valid, error = validate_password_strength(long_password)
        assert valid is False
        assert "128 characters" in error

    def test_password_missing_uppercase(self):
        """Test that passwords without uppercase fail."""
        valid, error = validate_password_strength("lowercase123!")
        assert valid is False
        assert "uppercase" in error.lower()

    def test_password_missing_lowercase(self):
        """Test that passwords without lowercase fail."""
        valid, error = validate_password_strength("UPPERCASE123!")
        assert valid is False
        assert "lowercase" in error.lower()

    def test_password_missing_number(self):
        """Test that passwords without numbers fail."""
        valid, error = validate_password_strength("NoNumbers!")
        assert valid is False
        assert "number" in error.lower()

    def test_password_missing_special_char(self):
        """Test that passwords without special characters fail."""
        valid, error = validate_password_strength("NoSpecialChar123")
        assert valid is False
        assert "special character" in error.lower()

    def test_various_special_characters_accepted(self):
        """Test that various special characters are accepted."""
        special_chars = ["!", "@", "#", "$", "%", "^", "&", "*", "(", ")", "-", "_", "+", "="]

        for char in special_chars:
            password = f"Password123{char}"
            valid, error = validate_password_strength(password)
            assert valid is True, f"Special character '{char}' should be valid"

    def test_minimum_valid_password(self):
        """Test minimum valid password (exactly 8 chars, all requirements)."""
        valid, error = validate_password_strength("Abc123!@")
        assert valid is True
        assert error == ""


class TestPasswordRequirements:
    """Test password requirements getter."""

    def test_get_password_requirements_structure(self):
        """Test that password requirements are returned correctly."""
        reqs = get_password_requirements()

        assert isinstance(reqs, dict)
        assert reqs["min_length"] == 8
        assert reqs["max_length"] == 128
        assert reqs["requires_uppercase"] is True
        assert reqs["requires_lowercase"] is True
        assert reqs["requires_number"] is True
        assert reqs["requires_special_char"] is True
        assert "special_chars" in reqs


class TestPasswordHashingSecurity:
    """Test security aspects of password hashing."""

    def test_bcrypt_with_12_rounds(self):
        """Test that bcrypt uses 12 rounds as per security requirements."""
        password = "TestPassword123!"
        hashed = hash_password(password)

        # Bcrypt hash format: $2b$12$... where 12 is the cost factor
        assert hashed.startswith("$2b$12$"), "Should use 12 rounds (cost factor)"

    def test_empty_password_can_be_hashed(self):
        """Test that empty passwords can be hashed (but would fail validation)."""
        hashed = hash_password("")
        assert len(hashed) > 0
        assert verify_password("", hashed) is True

    def test_unicode_password_support(self):
        """Test that unicode characters in passwords are supported."""
        password = "Pässwörd123!🔒"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
