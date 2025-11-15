"""
Pytest configuration and fixtures.

This module provides common test fixtures for the test suite.
"""

import os
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Set test environment
os.environ["ENVIRONMENT"] = "development"
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/test_zapcut_db"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"
os.environ["LOG_LEVEL"] = "ERROR"  # Reduce log noise during tests

from app.main import create_app
from app.database import Base, get_db
from app.config import settings


# Test database engine
TEST_DATABASE_URL = settings.database_url.replace("zapcut_db_dev", "test_zapcut_db")
test_engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def db_engine():
    """Create test database engine."""
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db(db_engine) -> Generator[Session, None, None]:
    """
    Create a new database session for a test.

    This fixture creates a new database session for each test and
    rolls back the transaction after the test completes.
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """
    Create a test client for the FastAPI application.

    This fixture provides a TestClient that uses the test database session.
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "testpassword123"
    }


@pytest.fixture
def test_brand_data():
    """Sample brand data for testing."""
    return {
        "name": "Test Brand",
        "description": "A test brand for testing purposes"
    }


@pytest.fixture
def test_project_data():
    """Sample project data for testing."""
    return {
        "name": "Test Project",
        "description": "A test ad project",
        "brand_id": 1
    }
