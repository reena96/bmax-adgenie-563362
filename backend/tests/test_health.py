"""
Tests for health check endpoints.
"""

import pytest
from fastapi.testclient import TestClient


def test_health_check_endpoint(client: TestClient):
    """Test the main health check endpoint."""
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert "status" in data
    assert "timestamp" in data
    assert "service" in data
    assert "version" in data
    assert "environment" in data
    assert "dependencies" in data

    # Check service info
    assert data["service"] == "Zapcut Ad Generation API"
    assert data["version"] == "0.1.0"
    assert data["environment"] == "development"

    # Check dependencies
    assert "database" in data["dependencies"]
    assert "redis" in data["dependencies"]


def test_readiness_check_endpoint(client: TestClient):
    """Test the readiness check endpoint."""
    response = client.get("/api/health/ready")

    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert "ready" in data
    assert "timestamp" in data or "reason" in data


def test_liveness_check_endpoint(client: TestClient):
    """Test the liveness check endpoint."""
    response = client.get("/api/health/live")

    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert "alive" in data
    assert data["alive"] is True
    assert "timestamp" in data


def test_root_endpoint(client: TestClient):
    """Test the root endpoint."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert "name" in data
    assert "version" in data
    assert "environment" in data
    assert "docs" in data
    assert "health" in data

    # Check values
    assert data["name"] == "Zapcut Ad Generation API"
    assert data["version"] == "0.1.0"
    assert data["docs"] == "/docs"
    assert data["health"] == "/api/health"


@pytest.mark.integration
def test_health_check_with_database(client: TestClient, db):
    """Test health check when database is available."""
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()

    # When database is available, status should be healthy or degraded
    # (degraded if Redis is not available)
    assert data["status"] in ["healthy", "degraded"]


def test_api_docs_available(client: TestClient):
    """Test that API documentation is available."""
    response = client.get("/docs")
    assert response.status_code == 200

    response = client.get("/redoc")
    assert response.status_code == 200
