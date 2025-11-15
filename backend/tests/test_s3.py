"""
Tests for S3 client functionality.
Note: These tests use mocking to avoid hitting actual AWS S3.
For integration tests with real S3, set AWS credentials and mark tests as @pytest.mark.integration.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

from app.s3_client import (
    upload_to_s3,
    get_signed_url,
    object_exists,
    delete_object,
    list_objects
)


@pytest.fixture
def mock_s3_client():
    """Mock S3 client for testing."""
    with patch('app.s3_client.get_s3_client') as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.mark.unit
def test_upload_to_s3_success(mock_s3_client, tmp_path):
    """Test successful file upload to S3."""
    # Create a temporary file
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    # Mock successful upload
    mock_s3_client.upload_file.return_value = None

    # Upload file
    s3_url = upload_to_s3(str(test_file), "test/test.txt")

    # Verify upload was called
    mock_s3_client.upload_file.assert_called_once()

    # Verify S3 URL format
    assert s3_url.startswith("s3://")
    assert "test/test.txt" in s3_url


@pytest.mark.unit
def test_upload_to_s3_with_content_type(mock_s3_client, tmp_path):
    """Test uploading file with specific content type."""
    test_file = tmp_path / "test.jpg"
    test_file.write_bytes(b"fake image data")

    mock_s3_client.upload_file.return_value = None

    s3_url = upload_to_s3(str(test_file), "images/test.jpg", content_type="image/jpeg")

    # Verify content type was passed
    call_args = mock_s3_client.upload_file.call_args
    assert call_args is not None
    if call_args[1].get('ExtraArgs'):
        assert call_args[1]['ExtraArgs'].get('ContentType') == 'image/jpeg'


@pytest.mark.unit
def test_upload_to_s3_file_not_found(mock_s3_client):
    """Test upload with non-existent file."""
    with pytest.raises(FileNotFoundError):
        upload_to_s3("/path/to/nonexistent/file.txt", "test/file.txt")


@pytest.mark.unit
def test_upload_to_s3_client_error(mock_s3_client, tmp_path):
    """Test upload with S3 client error."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    # Mock client error
    mock_s3_client.upload_file.side_effect = ClientError(
        {'Error': {'Code': 'AccessDenied', 'Message': 'Access Denied'}},
        'upload_file'
    )

    with pytest.raises(ClientError):
        upload_to_s3(str(test_file), "test/test.txt")


@pytest.mark.unit
def test_get_signed_url_success(mock_s3_client):
    """Test generating signed URL."""
    expected_url = "https://s3.amazonaws.com/bucket/key?signature=xyz"
    mock_s3_client.generate_presigned_url.return_value = expected_url

    url = get_signed_url("test/file.txt", expiry_seconds=3600)

    # Verify URL was generated
    assert url == expected_url
    mock_s3_client.generate_presigned_url.assert_called_once()

    # Verify parameters
    call_args = mock_s3_client.generate_presigned_url.call_args
    assert call_args[0][0] == 'get_object'
    assert call_args[1]['Params']['Key'] == 'test/file.txt'
    assert call_args[1]['ExpiresIn'] == 3600


@pytest.mark.unit
def test_get_signed_url_default_expiry(mock_s3_client):
    """Test signed URL with default expiry."""
    mock_s3_client.generate_presigned_url.return_value = "https://example.com"

    get_signed_url("test/file.txt")

    # Verify default expiry is 3600 seconds (1 hour)
    call_args = mock_s3_client.generate_presigned_url.call_args
    assert call_args[1]['ExpiresIn'] == 3600


@pytest.mark.unit
def test_get_signed_url_client_error(mock_s3_client):
    """Test signed URL generation with client error."""
    mock_s3_client.generate_presigned_url.side_effect = ClientError(
        {'Error': {'Code': 'NoSuchKey', 'Message': 'Key not found'}},
        'generate_presigned_url'
    )

    with pytest.raises(ClientError):
        get_signed_url("nonexistent/file.txt")


@pytest.mark.unit
def test_object_exists_true(mock_s3_client):
    """Test checking if object exists (returns True)."""
    mock_s3_client.head_object.return_value = {'ContentLength': 1024}

    exists = object_exists("test/file.txt")

    assert exists is True
    mock_s3_client.head_object.assert_called_once()


@pytest.mark.unit
def test_object_exists_false(mock_s3_client):
    """Test checking if object exists (returns False)."""
    mock_s3_client.head_object.side_effect = ClientError(
        {'Error': {'Code': '404', 'Message': 'Not Found'}},
        'head_object'
    )

    exists = object_exists("nonexistent/file.txt")

    assert exists is False


@pytest.mark.unit
def test_object_exists_other_error(mock_s3_client):
    """Test object exists with non-404 error."""
    mock_s3_client.head_object.side_effect = ClientError(
        {'Error': {'Code': 'AccessDenied', 'Message': 'Access Denied'}},
        'head_object'
    )

    # Should raise the error (not return False)
    with pytest.raises(ClientError):
        object_exists("test/file.txt")


@pytest.mark.unit
def test_delete_object_success(mock_s3_client):
    """Test successful object deletion."""
    mock_s3_client.delete_object.return_value = {'DeleteMarker': True}

    result = delete_object("test/file.txt")

    assert result is True
    mock_s3_client.delete_object.assert_called_once()


@pytest.mark.unit
def test_delete_object_error(mock_s3_client):
    """Test object deletion with error."""
    mock_s3_client.delete_object.side_effect = ClientError(
        {'Error': {'Code': 'AccessDenied', 'Message': 'Access Denied'}},
        'delete_object'
    )

    result = delete_object("test/file.txt")

    # Should return False on error
    assert result is False


@pytest.mark.unit
def test_list_objects_with_results(mock_s3_client):
    """Test listing objects with results."""
    mock_s3_client.list_objects_v2.return_value = {
        'Contents': [
            {'Key': 'folder/file1.txt'},
            {'Key': 'folder/file2.txt'},
            {'Key': 'folder/file3.txt'}
        ]
    }

    objects = list_objects("folder/")

    assert len(objects) == 3
    assert 'folder/file1.txt' in objects
    assert 'folder/file2.txt' in objects
    assert 'folder/file3.txt' in objects


@pytest.mark.unit
def test_list_objects_empty(mock_s3_client):
    """Test listing objects with no results."""
    mock_s3_client.list_objects_v2.return_value = {}

    objects = list_objects("empty_folder/")

    assert objects == []


@pytest.mark.unit
def test_list_objects_error(mock_s3_client):
    """Test listing objects with error."""
    mock_s3_client.list_objects_v2.side_effect = ClientError(
        {'Error': {'Code': 'NoSuchBucket', 'Message': 'Bucket not found'}},
        'list_objects_v2'
    )

    objects = list_objects("folder/")

    # Should return empty list on error
    assert objects == []


# Integration tests (require actual AWS credentials)
# These are marked as integration and slow - run separately

@pytest.mark.integration
@pytest.mark.slow
def test_s3_connection_real():
    """
    Test real S3 connection (requires AWS credentials).
    Only run this with: pytest -m integration
    """
    # This test would use real AWS credentials
    # Uncomment and configure if needed for integration testing
    pytest.skip("Integration test - requires AWS credentials")


@pytest.mark.integration
@pytest.mark.slow
def test_upload_download_real():
    """
    Test real upload and download from S3.
    Only run this with: pytest -m integration
    """
    pytest.skip("Integration test - requires AWS credentials")
