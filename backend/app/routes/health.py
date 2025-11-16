"""
Health check endpoints.

This module provides health check endpoints to monitor the status
of the API and its dependencies (database, Redis, etc.).
"""

import time
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, status
from pydantic import BaseModel

from app.config import settings
from app.database import check_database_connection

router = APIRouter()


async def check_s3_connection() -> tuple[bool, float]:
    """
    Check if S3 connection is healthy.

    Returns:
        Tuple of (is_connected, latency_ms)
    """
    try:
        from app.services.s3_service import get_s3_service
        start_time = time.time()
        s3_service = get_s3_service()
        is_connected = await s3_service.check_connection()
        latency_ms = (time.time() - start_time) * 1000
        return is_connected, latency_ms
    except Exception:
        return False, 0.0


class DependencyStatus(BaseModel):
    """Status information for a dependency."""
    status: str
    latency_ms: float | None = None


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: str
    service: str
    version: str
    environment: str
    dependencies: Dict[str, DependencyStatus]


def check_redis_connection() -> tuple[bool, float]:
    """
    Check if Redis connection is healthy.

    Returns:
        Tuple of (is_connected, latency_ms)
    """
    try:
        import redis
        start_time = time.time()
        client = redis.from_url(settings.redis_url, decode_responses=True)
        client.ping()
        latency_ms = (time.time() - start_time) * 1000
        client.close()
        return True, latency_ms
    except Exception:
        return False, 0.0


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check the health status of the API and its dependencies"
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns the status of the API and all its dependencies including:
    - Database connection
    - Redis connection
    - Service metadata (version, environment)

    Returns:
        HealthResponse with status information
    """
    # Check database
    db_connected, db_latency = check_database_connection()
    db_status = DependencyStatus(
        status="connected" if db_connected else "disconnected",
        latency_ms=db_latency if db_connected else None
    )

    # Check Redis
    redis_connected, redis_latency = check_redis_connection()
    redis_status = DependencyStatus(
        status="connected" if redis_connected else "disconnected",
        latency_ms=redis_latency if redis_connected else None
    )

    # Check S3
    s3_connected, s3_latency = await check_s3_connection()
    s3_status = DependencyStatus(
        status="connected" if s3_connected else "disconnected",
        latency_ms=s3_latency if s3_connected else None
    )

    # Determine overall status
    # S3 is optional - degraded if DB or Redis down, healthy if only S3 down
    critical_services_ok = db_connected and redis_connected
    overall_status = "healthy" if critical_services_ok and s3_connected else "degraded"

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(timezone.utc).isoformat(),
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        dependencies={
            "database": db_status,
            "redis": redis_status,
            "s3": s3_status,
        }
    )


@router.get(
    "/health/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness Check",
    description="Check if the service is ready to accept requests"
)
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint.

    This endpoint checks if the service is ready to accept traffic.
    It's typically used by orchestrators like Kubernetes.

    Returns:
        Dictionary with ready status
    """
    # Check if critical dependencies are available
    db_connected, _ = check_database_connection()

    if not db_connected:
        return {
            "ready": False,
            "reason": "Database not available"
        }

    return {
        "ready": True,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get(
    "/health/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness Check",
    description="Check if the service is alive"
)
async def liveness_check() -> Dict[str, str]:
    """
    Liveness check endpoint.

    This endpoint simply returns a 200 OK to indicate the service is running.
    It's typically used by orchestrators like Kubernetes.

    Returns:
        Dictionary with alive status
    """
    return {
        "alive": True,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
