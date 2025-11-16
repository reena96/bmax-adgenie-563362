"""
Tests for S3 upload service and asset endpoints.

This module tests the S3Service class and asset upload/presigned URL endpoints
using moto for S3 mocking.
"""

import pytest
import boto3
from io import BytesIO
from uuid import uuid4
from moto import mock_aws
from fastapi import UploadFile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.services.s3_service import S3Service
from app.services.file_validation import FileValidator
from app.exceptions import S3UploadError, S3ConnectionError, InvalidFileError
from app.models.asset import Asset
from app.database import Base


# Test fixtures
@pytest.fixture
def mock_s3():
    """Mock AWS S3 for testing."""
    with mock_aws():
        # Create mock S3 bucket
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')
        yield s3_client


@pytest.fixture
def s3_service(mock_s3):
    """Create S3Service instance with mock S3."""
    return S3Service(
        bucket_name='test-bucket',
        region='us-east-1',
        access_key='test-key',
        secret_key='test-secret'
    )


@pytest.fixture
def test_db():
    """Create in-memory SQLite database for testing."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


def create_upload_file(filename: str, content: bytes, content_type: str) -> UploadFile:
    """Helper to create UploadFile object for testing."""
    file = BytesIO(content)
    return UploadFile(filename=filename, file=file, content_type=content_type)


class TestS3Service:
    """Test suite for S3Service class."""

    # Valid test file content
    VALID_JPEG = b'\xff\xd8\xff\xe0' + b'\x00' * 1000
    VALID_PNG = b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a' + b'\x00' * 1000
    VALID_MP4 = b'\x00\x00\x00\x20\x66\x74\x79\x70' + b'\x00' * 1000

    @pytest.mark.asyncio
    async def test_s3_service_initialization(self, s3_service):
        """Test S3Service initializes correctly."""
        assert s3_service.bucket_name == 'test-bucket'
        assert s3_service.region == 'us-east-1'
        assert s3_service.s3_client is not None

    @pytest.mark.asyncio
    async def test_s3_service_missing_bucket_name(self):
        """Test S3Service raises error when bucket name is missing."""
        with pytest.raises(S3ConnectionError) as exc_info:
            S3Service(bucket_name=None, region='us-east-1')
        assert "bucket name not configured" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_upload_file_success(self, s3_service):
        """Test successful file upload to S3."""
        file = create_upload_file(
            "test.jpg",
            self.VALID_JPEG,
            "image/jpeg"
        )

        user_id = str(uuid4())
        result = await s3_service.upload_file(
            file=file,
            asset_type='brand_image',
            user_id=user_id
        )

        assert 's3_key' in result
        assert 's3_url' in result
        assert 'file_size' in result
        assert 'content_type' in result
        assert 'content_hash' in result
        assert result['file_size'] == len(self.VALID_JPEG)
        assert result['content_type'] == 'image/jpeg'
        assert 'brand-images' in result['s3_key']
        assert user_id in result['s3_key']

    @pytest.mark.asyncio
    async def test_upload_file_without_filename(self, s3_service):
        """Test upload fails when file has no filename."""
        file = create_upload_file("", self.VALID_JPEG, "image/jpeg")
        file.filename = None

        user_id = str(uuid4())
        with pytest.raises(InvalidFileError) as exc_info:
            await s3_service.upload_file(
                file=file,
                asset_type='brand_image',
                user_id=user_id
            )
        assert "no filename" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_upload_video_file(self, s3_service):
        """Test successful video file upload."""
        file = create_upload_file(
            "test_video.mp4",
            self.VALID_MP4,
            "video/mp4"
        )

        user_id = str(uuid4())
        project_id = str(uuid4())
        result = await s3_service.upload_file(
            file=file,
            asset_type='generated_video',
            user_id=user_id,
            project_id=project_id
        )

        assert 'generated-videos' in result['s3_key']
        assert project_id in result['s3_key']

    @pytest.mark.asyncio
    async def test_generate_s3_key_brand_image(self, s3_service):
        """Test S3 key generation for brand images."""
        user_id = str(uuid4())
        s3_key = s3_service._generate_s3_key(
            filename="test image.jpg",
            asset_type="brand_image",
            user_id=user_id
        )

        assert s3_key.startswith(f"brand-images/{user_id}/")
        assert "test_image.jpg" in s3_key  # Sanitized filename
        assert s3_key.count('_') >= 2  # timestamp_uuid_filename

    @pytest.mark.asyncio
    async def test_generate_s3_key_generated_video(self, s3_service):
        """Test S3 key generation for generated videos."""
        user_id = str(uuid4())
        project_id = str(uuid4())
        s3_key = s3_service._generate_s3_key(
            filename="final_ad.mp4",
            asset_type="generated_video",
            user_id=user_id,
            project_id=project_id
        )

        assert s3_key.startswith(f"generated-videos/{project_id}/")
        assert "final_ad.mp4" in s3_key

    @pytest.mark.asyncio
    async def test_get_presigned_url(self, s3_service, mock_s3):
        """Test presigned URL generation."""
        # First upload a file
        s3_key = "test-files/test.jpg"
        mock_s3.put_object(
            Bucket='test-bucket',
            Key=s3_key,
            Body=self.VALID_JPEG
        )

        # Generate presigned URL
        result = await s3_service.get_presigned_url(
            s3_key=s3_key,
            expiration_hours=24
        )

        assert 'presigned_url' in result
        assert 'expiration_at' in result
        assert 'test-bucket' in result['presigned_url']
        assert s3_key in result['presigned_url']

    @pytest.mark.asyncio
    async def test_get_presigned_url_invalid_expiration(self, s3_service):
        """Test presigned URL generation fails with invalid expiration."""
        with pytest.raises(ValueError) as exc_info:
            await s3_service.get_presigned_url(
                s3_key="test.jpg",
                expiration_hours=200  # > 168 hours (7 days)
            )
        assert "cannot exceed" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_delete_file(self, s3_service, mock_s3):
        """Test file deletion from S3."""
        # First upload a file
        s3_key = "test-files/delete-me.jpg"
        mock_s3.put_object(
            Bucket='test-bucket',
            Key=s3_key,
            Body=self.VALID_JPEG
        )

        # Delete the file
        result = await s3_service.delete_file(s3_key)
        assert result is True

        # Verify file is deleted
        objects = mock_s3.list_objects_v2(Bucket='test-bucket', Prefix=s3_key)
        assert 'Contents' not in objects

    @pytest.mark.asyncio
    async def test_check_connection_success(self, s3_service):
        """Test S3 connection check succeeds."""
        result = await s3_service.check_connection()
        assert result is True

    @pytest.mark.asyncio
    async def test_get_cache_control_brand_image(self, s3_service):
        """Test cache control for brand images."""
        cache_control = s3_service._get_cache_control('brand_image')
        assert 'immutable' in cache_control
        assert '31536000' in cache_control  # 1 year

    @pytest.mark.asyncio
    async def test_get_cache_control_generated_video(self, s3_service):
        """Test cache control for generated videos."""
        cache_control = s3_service._get_cache_control('generated_video')
        assert 'no-cache' in cache_control

    @pytest.mark.asyncio
    async def test_upload_with_metadata(self, s3_service, mock_s3):
        """Test file upload includes proper metadata."""
        file = create_upload_file(
            "test.jpg",
            self.VALID_JPEG,
            "image/jpeg"
        )

        user_id = str(uuid4())
        result = await s3_service.upload_file(
            file=file,
            asset_type='brand_image',
            user_id=user_id
        )

        # Verify metadata in S3
        s3_object = mock_s3.head_object(
            Bucket='test-bucket',
            Key=result['s3_key']
        )

        assert s3_object['Metadata']['uploaded_by'] == user_id
        assert s3_object['Metadata']['asset_type'] == 'brand_image'
        assert 'upload_timestamp' in s3_object['Metadata']
        assert s3_object['ServerSideEncryption'] == 'AES256'

    @pytest.mark.asyncio
    async def test_concurrent_uploads(self, s3_service):
        """Test multiple concurrent file uploads."""
        import asyncio

        files = [
            create_upload_file(f"test{i}.jpg", self.VALID_JPEG, "image/jpeg")
            for i in range(5)
        ]

        user_id = str(uuid4())
        upload_tasks = [
            s3_service.upload_file(
                file=file,
                asset_type='brand_image',
                user_id=user_id
            )
            for file in files
        ]

        results = await asyncio.gather(*upload_tasks)

        assert len(results) == 5
        # Verify all have unique S3 keys
        s3_keys = [r['s3_key'] for r in results]
        assert len(set(s3_keys)) == 5

    @pytest.mark.asyncio
    async def test_upload_file_with_special_characters(self, s3_service):
        """Test file upload sanitizes special characters in filename."""
        file = create_upload_file(
            "test file!@#$%^&*().jpg",
            self.VALID_JPEG,
            "image/jpeg"
        )

        user_id = str(uuid4())
        result = await s3_service.upload_file(
            file=file,
            asset_type='brand_image',
            user_id=user_id
        )

        # Verify special characters are sanitized
        assert '!' not in result['s3_key']
        assert '@' not in result['s3_key']
        assert '#' not in result['s3_key']
