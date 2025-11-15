"""
Redis connection and RQ (Redis Queue) setup.
"""
import redis
from rq import Queue
from typing import Optional

from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# Redis connection instance
redis_client: Optional[redis.Redis] = None
# RQ Queue instance
job_queue: Optional[Queue] = None


def get_redis_client() -> redis.Redis:
    """
    Get or create Redis client instance.

    Returns:
        Redis client instance
    """
    global redis_client

    if redis_client is None:
        try:
            redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    return redis_client


def get_job_queue() -> Queue:
    """
    Get or create RQ job queue instance.

    Returns:
        RQ Queue instance
    """
    global job_queue

    if job_queue is None:
        client = get_redis_client()
        job_queue = Queue(connection=client, default_timeout=3600)
        logger.info("RQ job queue initialized")

    return job_queue


def check_redis_connection() -> bool:
    """
    Check if Redis connection is working.

    Returns:
        True if connection is successful, False otherwise
    """
    try:
        client = get_redis_client()
        client.ping()
        return True
    except Exception as e:
        logger.error(f"Redis connection check failed: {e}")
        return False


def enqueue_job(func, *args, **kwargs):
    """
    Enqueue a job to the default queue.

    Args:
        func: Function to execute
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function

    Returns:
        RQ Job instance
    """
    queue = get_job_queue()
    job = queue.enqueue(func, *args, **kwargs)
    logger.info(f"Job {job.id} enqueued: {func.__name__}")
    return job
