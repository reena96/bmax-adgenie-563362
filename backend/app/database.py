"""
Database connection and session management.

This module configures SQLAlchemy for PostgreSQL connection pooling
and provides database session management for FastAPI routes.
"""

from typing import Generator, AsyncGenerator
from sqlalchemy import create_engine, event, Engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import Pool
import time
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy engine with connection pooling
engine = create_engine(
    settings.get_database_url(async_driver=False),
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,  # Verify connections before using them
    echo=settings.is_development,  # Log SQL in development
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for SQLAlchemy models
Base = declarative_base()


# Event listeners for connection pool monitoring
@event.listens_for(Pool, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Log when a new database connection is created."""
    logger.debug("Database connection established")


@event.listens_for(Pool, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Log when a connection is checked out from the pool."""
    logger.debug("Database connection checked out from pool")


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions.

    Provides a database session that is automatically closed after use.
    Use this as a dependency in FastAPI routes.

    Yields:
        Database session

    Example:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> tuple[bool, float]:
    """
    Check if database connection is healthy.

    Returns:
        Tuple of (is_connected, latency_ms)
    """
    try:
        start_time = time.time()
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        latency_ms = (time.time() - start_time) * 1000
        return True, latency_ms
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False, 0.0


def init_db() -> None:
    """
    Initialize database tables.

    This creates all tables defined in models.
    In production, use Alembic migrations instead.
    """
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")


def get_db_info() -> dict:
    """
    Get database connection information.

    Returns:
        Dictionary with database info
    """
    return {
        "url": settings.database_url.split("@")[-1],  # Hide credentials
        "pool_size": settings.db_pool_size,
        "max_overflow": settings.db_max_overflow,
        "dialect": engine.dialect.name,
        "driver": engine.driver,
    }
