"""
Tests for health check endpoint.
"""
import pytest
from datetime import datetime


@pytest.mark.unit
def test_health_check_returns_200(client):
    """Test that health check endpoint returns 200 status code."""
    response = client.get("/api/health")
    assert response.status_code == 200


@pytest.mark.unit
def test_health_check_response_format(client):
    """Test that health check returns correct JSON format."""
    response = client.get("/api/health")
    data = response.json()

    # Check required fields
    assert "status" in data
    assert "timestamp" in data
    assert "db_connected" in data
    assert "redis_connected" in data

    # Check field types
    assert isinstance(data["status"], str)
    assert isinstance(data["db_connected"], bool)
    assert isinstance(data["redis_connected"], bool)

    # Verify timestamp is valid ISO format
    timestamp = data["timestamp"]
    assert isinstance(timestamp, str)
    # Should be parseable as datetime
    datetime.fromisoformat(timestamp.replace('Z', '+00:00'))


@pytest.mark.unit
def test_health_check_includes_db_status(client):
    """Test that health check includes database connectivity status."""
    response = client.get("/api/health")
    data = response.json()

    assert "db_connected" in data
    # For in-memory SQLite in tests, this should be True
    assert isinstance(data["db_connected"], bool)


@pytest.mark.unit
def test_health_check_includes_redis_status(client):
    """Test that health check includes Redis connectivity status."""
    response = client.get("/api/health")
    data = response.json()

    assert "redis_connected" in data
    assert isinstance(data["redis_connected"], bool)


@pytest.mark.unit
def test_health_check_status_field(client):
    """Test that status field contains valid values."""
    response = client.get("/api/health")
    data = response.json()

    status = data["status"]
    # Status should be either 'healthy' or 'degraded'
    assert status in ["healthy", "degraded"]
