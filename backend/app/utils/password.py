"""
Password utilities for hashing, verification, and strength validation.

Uses bcrypt with 12 salt rounds for secure password hashing.
Implements password strength requirements:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character
"""
import re
from passlib.context import CryptContext

# Bcrypt context with 12 salt rounds (as per security requirements)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with 12 salt rounds.

    Args:
        password: Plain text password to hash

    Returns:
        Hashed password string

    Example:
        >>> hashed = hash_password("MySecure123!")
        >>> verify_password("MySecure123!", hashed)
        True
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a bcrypt hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Bcrypt hash to verify against

    Returns:
        True if password matches hash, False otherwise

    Example:
        >>> hashed = hash_password("MySecure123!")
        >>> verify_password("MySecure123!", hashed)
        True
        >>> verify_password("WrongPassword", hashed)
        False
    """
    return pwd_context.verify(plain_password, hashed_password)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength against security requirements.

    Requirements:
    - Minimum 8 characters
    - Maximum 128 characters
    - At least one uppercase letter (A-Z)
    - At least one lowercase letter (a-z)
    - At least one number (0-9)
    - At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid: bool, error_message: str)
        If valid, error_message is empty string

    Example:
        >>> validate_password_strength("weak")
        (False, "Password must be at least 8 characters long")
        >>> validate_password_strength("MySecure123!")
        (True, "")
    """
    # Check length
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if len(password) > 128:
        return False, "Password must be less than 128 characters"

    # Check for uppercase letter
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"

    # Check for lowercase letter
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"

    # Check for number
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"

    # Check for special character
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?/\\`~]', password):
        return False, "Password must contain at least one special character"

    return True, ""


def get_password_requirements() -> dict:
    """
    Get password requirements as a dictionary for API documentation.

    Returns:
        Dictionary describing password requirements

    Example:
        >>> reqs = get_password_requirements()
        >>> reqs['min_length']
        8
    """
    return {
        "min_length": 8,
        "max_length": 128,
        "requires_uppercase": True,
        "requires_lowercase": True,
        "requires_number": True,
        "requires_special_char": True,
        "special_chars": "!@#$%^&*()_+-=[]{}|;:,.<>?/\\`~"
    }
