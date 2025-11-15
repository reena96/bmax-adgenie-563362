"""
Custom exception classes for the application.

These exceptions are used throughout the application to handle
various error conditions with appropriate HTTP status codes.
"""

from typing import Any


class AppException(Exception):
    """Base exception class for all application exceptions."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: dict[str, Any] | None = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundException(AppException):
    """Exception raised when a resource is not found."""

    def __init__(self, message: str = "Resource not found", details: dict[str, Any] | None = None):
        super().__init__(message, status_code=404, details=details)


class BadRequestException(AppException):
    """Exception raised for bad requests."""

    def __init__(self, message: str = "Bad request", details: dict[str, Any] | None = None):
        super().__init__(message, status_code=400, details=details)


class UnauthorizedException(AppException):
    """Exception raised when authentication fails."""

    def __init__(self, message: str = "Unauthorized", details: dict[str, Any] | None = None):
        super().__init__(message, status_code=401, details=details)


class ForbiddenException(AppException):
    """Exception raised when access is forbidden."""

    def __init__(self, message: str = "Forbidden", details: dict[str, Any] | None = None):
        super().__init__(message, status_code=403, details=details)


class ConflictException(AppException):
    """Exception raised when there's a conflict (e.g., duplicate resource)."""

    def __init__(self, message: str = "Conflict", details: dict[str, Any] | None = None):
        super().__init__(message, status_code=409, details=details)


class ValidationException(AppException):
    """Exception raised for validation errors."""

    def __init__(self, message: str = "Validation error", details: dict[str, Any] | None = None):
        super().__init__(message, status_code=422, details=details)


class DatabaseException(AppException):
    """Exception raised for database errors."""

    def __init__(self, message: str = "Database error", details: dict[str, Any] | None = None):
        super().__init__(message, status_code=500, details=details)


class ExternalServiceException(AppException):
    """Exception raised when an external service fails."""

    def __init__(self, message: str = "External service error", details: dict[str, Any] | None = None):
        super().__init__(message, status_code=503, details=details)
