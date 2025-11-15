"""
Pytest configuration and fixtures.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, JSON
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects.postgresql import JSONB

from app.main import app
from app.models import Base
from app.database import get_db
from app.config import settings


# Test database URL (in-memory SQLite for fast tests)
TEST_DATABASE_URL = "sqlite:///:memory:"


# Replace JSONB columns with JSON and UUID with String for SQLite compatibility
def _convert_types_for_sqlite():
    """
    Convert JSONB columns to JSON and UUID to String for SQLite compatibility.
    """
    from sqlalchemy import String
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
    from app import models

    # Convert all JSONB and UUID columns in all models
    for model_class in [models.User, models.Brand, models.AdProject, models.Script,
                        models.GenerationJob, models.LoraModel, models.ChatMessage,
                        models.Session, models.PasswordReset]:
        table = model_class.__table__
        for column in table.columns:
            if isinstance(column.type, JSONB):
                column.type = JSON()
            elif isinstance(column.type, PG_UUID):
                column.type = String(36)


# Apply conversion before creating tables
_convert_types_for_sqlite()


@pytest.fixture(scope="function")
def test_db():
    """
    Create a test database for each test.
    Uses in-memory SQLite for speed.
    """
    # Create engine with in-memory SQLite
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session factory
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Yield session
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function", autouse=True)
def mock_redis(monkeypatch):
    """Mock Redis client for testing."""
    from unittest.mock import MagicMock

    mock_client = MagicMock()
    mock_client.exists.return_value = 0  # Token not blacklisted
    mock_client.setex.return_value = True
    mock_client.get.return_value = None
    mock_client.ping.return_value = True

    # Patch the get_redis_client function
    monkeypatch.setattr("app.redis_client.get_redis_client", lambda: mock_client)
    monkeypatch.setattr("app.security.get_redis_client", lambda: mock_client)

    yield mock_client


@pytest.fixture(scope="function")
def client(test_db, mock_redis):
    """
    Create a test client for FastAPI.
    Overrides the database dependency to use test database.
    """
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def test_user_data():
    """
    Sample user data for testing.
    """
    return {
        "email": "test@example.com",
        "name": "Test User",
        "password": "testpassword123"
    }


@pytest.fixture(scope="session")
def test_brand_data():
    """
    Sample brand data for testing.
    """
    return {
        "title": "Test Brand",
        "description": "A test brand for unit testing",
        "brand_guidelines": {
            "colors": ["#FF0000", "#00FF00"],
            "tone": "professional"
        }
    }


@pytest.fixture(scope="session")
def test_project_data():
    """
    Sample project data for testing.
    """
    return {
        "status": "draft",
        "ad_details": {
            "duration": 30,
            "style": "modern"
        }
    }
