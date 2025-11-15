"""
FastAPI application factory.

This module creates and configures the FastAPI application with all
middleware, routes, and event handlers.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.exceptions import AppException
from app.middleware.logging import LoggingMiddleware
from app.middleware.error_handler import (
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("=" * 60)
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Log Level: {settings.log_level}")
    logger.info("=" * 60)

    # Verify database connection
    from app.database import check_database_connection
    is_connected, latency = check_database_connection()
    if is_connected:
        logger.info(f"Database connected (latency: {latency:.2f}ms)")
    else:
        logger.warning("Database connection failed - some features may not work")

    yield

    # Shutdown
    logger.info("Shutting down application...")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title=settings.app_name,
        description="AI-powered ad generation backend for Zapcut",
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url, "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add logging middleware
    app.add_middleware(LoggingMiddleware)

    # Register exception handlers
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Register routes
    from app.routes.health import router as health_router
    from app.routes.auth import router as auth_router
    from app.routes.brands import router as brands_router
    from app.routes.projects import router as projects_router
    from app.routes.chat import router as chat_router
    from app.routes.scripts import router as scripts_router

    # Include routers with prefixes
    app.include_router(health_router, prefix="/api", tags=["Health"])
    app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(brands_router, prefix="/api/brands", tags=["Brands"])
    app.include_router(projects_router, prefix="/api/projects", tags=["Projects"])
    app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])
    app.include_router(scripts_router, prefix="/api/scripts", tags=["Scripts"])

    logger.info("FastAPI application created successfully")

    return app


# Create the app instance
app = create_app()


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/docs",
        "health": "/api/health",
    }
