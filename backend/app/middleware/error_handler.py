"""
Error handling middleware and exception handlers.

This module provides global exception handling for the FastAPI application,
ensuring all errors return consistent JSON responses.
"""

import logging
from typing import Union
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.exceptions import AppException

logger = logging.getLogger(__name__)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Handle custom application exceptions.

    Args:
        request: The incoming request
        exc: The application exception

    Returns:
        JSON response with error details
    """
    logger.error(
        f"Application error: {exc.message} - "
        f"Status: {exc.status_code} - "
        f"Path: {request.url.path}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path,
        }
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
) -> JSONResponse:
    """
    Handle HTTP exceptions.

    Args:
        request: The incoming request
        exc: The HTTP exception

    Returns:
        JSON response with error details
    """
    logger.error(
        f"HTTP error: {exc.detail} - "
        f"Status: {exc.status_code} - "
        f"Path: {request.url.path}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path,
        }
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle request validation errors.

    Args:
        request: The incoming request
        exc: The validation error

    Returns:
        JSON response with validation error details
    """
    logger.error(
        f"Validation error on {request.url.path}: {exc.errors()}"
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "details": exc.errors(),
            "path": request.url.path,
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all other unhandled exceptions.

    Args:
        request: The incoming request
        exc: The exception

    Returns:
        JSON response with generic error message
    """
    logger.exception(
        f"Unhandled exception on {request.url.path}: {str(exc)}"
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "An unexpected error occurred",
            "path": request.url.path,
        }
    )
