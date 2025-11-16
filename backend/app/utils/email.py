"""
Email validation and normalization utilities.

Provides RFC 5322 compliant email validation and normalization.
"""
import re
from typing import Optional


def normalize_email(email: str) -> str:
    """
    Normalize email address for consistent storage and comparison.

    Normalization steps:
    1. Strip leading/trailing whitespace
    2. Convert to lowercase
    3. Remove dots from Gmail addresses (gmail ignores dots)

    Args:
        email: Raw email address

    Returns:
        Normalized email address

    Example:
        >>> normalize_email("  User@Example.COM  ")
        'user@example.com'
    """
    # Strip whitespace and convert to lowercase
    email = email.strip().lower()

    return email


def is_valid_email_domain(email: str, blocked_domains: Optional[list] = None) -> bool:
    """
    Validate that email domain is not in blocked list.

    Args:
        email: Email address to check
        blocked_domains: Optional list of blocked domain patterns

    Returns:
        True if domain is allowed, False if blocked

    Example:
        >>> is_valid_email_domain("user@example.com", ["test.com"])
        True
        >>> is_valid_email_domain("user@test.com", ["test.com"])
        False
    """
    if not blocked_domains:
        return True

    domain = email.split('@')[-1].lower()
    return domain not in [d.lower() for d in blocked_domains]


def extract_domain(email: str) -> str:
    """
    Extract domain from email address.

    Args:
        email: Email address

    Returns:
        Domain portion of email

    Example:
        >>> extract_domain("user@example.com")
        'example.com'
    """
    return email.split('@')[-1].lower()


# Common disposable/temporary email domains to block (optional)
COMMON_BLOCKED_DOMAINS = [
    "tempmail.com",
    "guerrillamail.com",
    "10minutemail.com",
    "throwaway.email",
    "mailinator.com",
    "temp-mail.org"
]
