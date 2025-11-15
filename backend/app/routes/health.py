"""
Health check endpoint.
"""
from fastapi import APIRouter
from datetime import datetime

from app.schemas import HealthResponse
from app.database import check_db_connection
from app.redis_client import check_redis_connection

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    Returns the health status of the API and its dependencies.

    Returns:
        HealthResponse with status, timestamp, and dependency health
    """
    db_connected = check_db_connection()
    redis_connected = check_redis_connection()

    return HealthResponse(
        status="healthy" if (db_connected and redis_connected) else "degraded",
        timestamp=datetime.utcnow(),
        db_connected=db_connected,
        redis_connected=redis_connected
    )
