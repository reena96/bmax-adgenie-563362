"""
Tests for Redis client and RQ functionality.
Note: These tests use mocking to avoid requiring actual Redis server.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from app.redis_client import (
    get_redis_client,
    get_job_queue,
    check_redis_connection,
    enqueue_job
)


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch('app.redis_client.redis.from_url') as mock:
        client = MagicMock()
        client.ping.return_value = True
        mock.return_value = client
        yield client


@pytest.fixture
def mock_queue():
    """Mock RQ Queue."""
    with patch('app.redis_client.Queue') as mock:
        queue = MagicMock()
        mock.return_value = queue
        yield queue


@pytest.mark.unit
def test_redis_connection(mock_redis):
    """Test Redis connection establishment."""
    # Reset module state
    import app.redis_client
    app.redis_client.redis_client = None

    client = get_redis_client()

    assert client is not None
    mock_redis.ping.assert_called()


@pytest.mark.unit
def test_redis_connection_check_success(mock_redis):
    """Test Redis connection check when connected."""
    import app.redis_client
    app.redis_client.redis_client = None

    result = check_redis_connection()

    assert result is True


@pytest.mark.unit
def test_redis_connection_check_failure():
    """Test Redis connection check when connection fails."""
    with patch('app.redis_client.get_redis_client') as mock:
        mock.side_effect = Exception("Connection failed")

        result = check_redis_connection()

        assert result is False


@pytest.mark.unit
def test_get_job_queue(mock_redis, mock_queue):
    """Test RQ job queue initialization."""
    import app.redis_client
    app.redis_client.redis_client = None
    app.redis_client.job_queue = None

    queue = get_job_queue()

    assert queue is not None
    mock_queue.assert_called_once()


@pytest.mark.unit
def test_enqueue_job(mock_redis, mock_queue):
    """Test enqueueing a job."""
    import app.redis_client
    app.redis_client.redis_client = None
    app.redis_client.job_queue = None

    # Mock job
    mock_job = MagicMock()
    mock_job.id = "test_job_123"
    mock_queue.return_value.enqueue.return_value = mock_job

    # Test function to enqueue
    def test_task(x, y):
        return x + y

    job = enqueue_job(test_task, 1, 2)

    assert job is not None
    assert job.id == "test_job_123"


@pytest.mark.integration
@pytest.mark.slow
def test_redis_real_connection():
    """
    Test real Redis connection (requires Redis server).
    Only run this with: pytest -m integration
    """
    pytest.skip("Integration test - requires Redis server")


@pytest.mark.integration
@pytest.mark.slow
def test_rq_job_enqueue_real():
    """
    Test real RQ job enqueueing (requires Redis server).
    Only run this with: pytest -m integration
    """
    pytest.skip("Integration test - requires Redis server")
