"""
Unit tests for brand service business logic.
Tests service layer functions with mocked dependencies.
"""
import io
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from app.services import brand_service
from app.services.s3_service import (
    validate_image_file,
    validate_file_size,
    validate_image_count,
    upload_brand_images,
    delete_brand_images
)
from app.models import User, Brand, AdProject
from app.schemas import BrandCreate, BrandUpdate, BrandGuidelines


@pytest.fixture
def test_user(test_db):
    """Create a test user."""
    user_id = str(uuid4())
    user = User(
        id=user_id,
        email="testuser@example.com",
        name="Test User",
        password_hash="hashed",
        subscription_tier="free"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_brand(test_db, test_user):
    """Create a test brand."""
    brand_id = str(uuid4())
    brand = Brand(
        id=brand_id,
        user_id=test_user.id,
        title="Test Brand",
        description="Test Description",
        product_images=[
            "s3://bucket/image1.jpg",
            "s3://bucket/image2.jpg"
        ],
        brand_guidelines={
            "colors": ["#FF0000"],
            "tone": "professional"
        }
    )
    test_db.add(brand)
    test_db.commit()
    test_db.refresh(brand)
    return brand


def create_mock_upload_file(filename: str, content: bytes, content_type: str) -> UploadFile:
    """Helper to create a mock UploadFile."""
    file = MagicMock(spec=UploadFile)
    file.filename = filename
    file.content_type = content_type
    file.file = io.BytesIO(content)
    file.read = AsyncMock(return_value=content)
    return file


class TestS3ServiceValidation:
    """Tests for S3 service validation functions."""

    def test_validate_image_file_valid_jpeg(self):
        """Test validation accepts valid JPEG."""
        file = create_mock_upload_file("test.jpg", b"fake", "image/jpeg")
        # Should not raise exception
        validate_image_file(file)

    def test_validate_image_file_valid_png(self):
        """Test validation accepts valid PNG."""
        file = create_mock_upload_file("test.png", b"fake", "image/png")
        validate_image_file(file)

    def test_validate_image_file_valid_webp(self):
        """Test validation accepts valid WEBP."""
        file = create_mock_upload_file("test.webp", b"fake", "image/webp")
        validate_image_file(file)

    def test_validate_image_file_invalid_type(self):
        """Test validation rejects invalid file type."""
        file = create_mock_upload_file("test.pdf", b"fake", "application/pdf")
        with pytest.raises(HTTPException) as exc_info:
            validate_image_file(file)
        assert exc_info.value.status_code == 415

    def test_validate_image_file_invalid_extension(self):
        """Test validation rejects invalid extension."""
        file = create_mock_upload_file("test.gif", b"fake", "image/gif")
        with pytest.raises(HTTPException) as exc_info:
            validate_image_file(file)
        assert exc_info.value.status_code == 415

    def test_validate_file_size_valid(self):
        """Test file size validation accepts valid size."""
        content = b"x" * (5 * 1024 * 1024)  # 5MB
        file = create_mock_upload_file("test.jpg", content, "image/jpeg")
        validate_file_size(file)

    def test_validate_file_size_too_large(self):
        """Test file size validation rejects oversized file."""
        content = b"x" * (11 * 1024 * 1024)  # 11MB
        file = create_mock_upload_file("test.jpg", content, "image/jpeg")
        with pytest.raises(HTTPException) as exc_info:
            validate_file_size(file)
        assert exc_info.value.status_code == 413

    def test_validate_image_count_valid_min(self):
        """Test image count validation accepts minimum (2)."""
        validate_image_count(2)

    def test_validate_image_count_valid_max(self):
        """Test image count validation accepts maximum (10)."""
        validate_image_count(10)

    def test_validate_image_count_too_few(self):
        """Test image count validation rejects less than 2."""
        with pytest.raises(HTTPException) as exc_info:
            validate_image_count(1)
        assert exc_info.value.status_code == 400
        assert "Minimum 2 images" in str(exc_info.value.detail)

    def test_validate_image_count_too_many(self):
        """Test image count validation rejects more than 10."""
        with pytest.raises(HTTPException) as exc_info:
            validate_image_count(11)
        assert exc_info.value.status_code == 400
        assert "Maximum 10 images" in str(exc_info.value.detail)


class TestS3ServiceUpload:
    """Tests for S3 service upload functions."""

    @pytest.mark.asyncio
    async def test_upload_brand_images_success(self):
        """Test successful image upload to S3."""
        user_id = str(uuid4())
        brand_id = str(uuid4())

        images = [
            create_mock_upload_file("test1.jpg", b"fake1", "image/jpeg"),
            create_mock_upload_file("test2.png", b"fake2", "image/png")
        ]

        with patch("app.services.s3_service.get_s3_client") as mock_client:
            s3_mock = MagicMock()
            mock_client.return_value = s3_mock

            urls = await upload_brand_images(user_id, brand_id, images)

            assert len(urls) == 2
            assert all(url.startswith("s3://") for url in urls)
            assert s3_mock.put_object.call_count == 2

    @pytest.mark.asyncio
    async def test_upload_brand_images_validation_failure(self):
        """Test upload fails with invalid images."""
        user_id = str(uuid4())
        brand_id = str(uuid4())

        # Only 1 image (less than minimum 2)
        images = [
            create_mock_upload_file("test1.jpg", b"fake", "image/jpeg")
        ]

        with pytest.raises(HTTPException) as exc_info:
            await upload_brand_images(user_id, brand_id, images)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_brand_images_s3_failure(self):
        """Test upload handles S3 failure gracefully."""
        from botocore.exceptions import ClientError

        user_id = str(uuid4())
        brand_id = str(uuid4())

        images = [
            create_mock_upload_file("test1.jpg", b"fake1", "image/jpeg"),
            create_mock_upload_file("test2.jpg", b"fake2", "image/jpeg")
        ]

        with patch("app.services.s3_service.get_s3_client") as mock_client:
            s3_mock = MagicMock()
            s3_mock.put_object.side_effect = ClientError(
                {"Error": {"Code": "500", "Message": "S3 Error"}},
                "put_object"
            )
            mock_client.return_value = s3_mock

            with pytest.raises(HTTPException) as exc_info:
                await upload_brand_images(user_id, brand_id, images)
            assert exc_info.value.status_code == 500

    def test_delete_brand_images(self):
        """Test deleting brand images from S3."""
        urls = [
            "s3://bucket/brands/user1/brand1/image1.jpg",
            "s3://bucket/brands/user1/brand1/image2.jpg"
        ]

        with patch("app.services.s3_service.delete_object") as mock_delete:
            delete_brand_images(urls)
            assert mock_delete.call_count == 2


class TestBrandServiceCreate:
    """Tests for brand service create function."""

    @pytest.mark.asyncio
    async def test_create_brand_success(self, test_db, test_user):
        """Test successful brand creation."""
        brand_data = BrandCreate(
            title="New Brand",
            description="Brand description",
            brand_guidelines=BrandGuidelines(
                colors=["#FF0000"],
                tone="professional"
            )
        )

        images = [
            create_mock_upload_file("test1.jpg", b"fake1", "image/jpeg"),
            create_mock_upload_file("test2.jpg", b"fake2", "image/jpeg")
        ]

        with patch("app.services.brand_service.upload_brand_images") as mock_upload:
            mock_upload.return_value = [
                "s3://bucket/image1.jpg",
                "s3://bucket/image2.jpg"
            ]

            result = await brand_service.create_brand(test_db, test_user.id, brand_data, images)

            assert result.title == "New Brand"
            assert result.description == "Brand description"
            assert len(result.product_images) == 2
            assert result.brand_guidelines["tone"] == "professional"


class TestBrandServiceList:
    """Tests for brand service list function."""

    def test_get_user_brands_success(self, test_db, test_user):
        """Test getting user's brands."""
        # Create test brands
        for i in range(3):
            brand = Brand(
                id=str(uuid4()),
                user_id=test_user.id,
                title=f"Brand {i}",
                product_images=[f"s3://bucket/image{i}.jpg", f"s3://bucket/image{i}_2.jpg"]
            )
            test_db.add(brand)
        test_db.commit()

        result = brand_service.get_user_brands(test_db, test_user.id, page=1, limit=20)

        assert len(result.brands) == 3
        assert result.pagination.total == 3
        assert result.pagination.page == 1
        assert result.pagination.has_more is False

    def test_get_user_brands_pagination(self, test_db, test_user):
        """Test brand listing pagination."""
        # Create 5 brands
        for i in range(5):
            brand = Brand(
                id=str(uuid4()),
                user_id=test_user.id,
                title=f"Brand {i}",
                product_images=["s3://bucket/image.jpg", "s3://bucket/image2.jpg"]
            )
            test_db.add(brand)
        test_db.commit()

        # Page 1
        result = brand_service.get_user_brands(test_db, test_user.id, page=1, limit=2)
        assert len(result.brands) == 2
        assert result.pagination.has_more is True

        # Page 2
        result = brand_service.get_user_brands(test_db, test_user.id, page=2, limit=2)
        assert len(result.brands) == 2
        assert result.pagination.has_more is True

        # Page 3
        result = brand_service.get_user_brands(test_db, test_user.id, page=3, limit=2)
        assert len(result.brands) == 1
        assert result.pagination.has_more is False


class TestBrandServiceGet:
    """Tests for brand service get function."""

    def test_get_brand_by_id_success(self, test_db, test_user, test_brand):
        """Test getting brand by ID."""
        result = brand_service.get_brand_by_id(test_db, test_brand.id, test_user.id)

        assert result.id == test_brand.id
        assert result.title == test_brand.title

    def test_get_brand_by_id_not_found(self, test_db, test_user):
        """Test getting non-existent brand returns 404."""
        fake_id = str(uuid4())

        with pytest.raises(HTTPException) as exc_info:
            brand_service.get_brand_by_id(test_db, fake_id, test_user.id)
        assert exc_info.value.status_code == 404

    def test_get_brand_by_id_ownership_violation(self, test_db, test_brand):
        """Test getting brand with wrong user returns 403."""
        other_user_id = str(uuid4())

        with pytest.raises(HTTPException) as exc_info:
            brand_service.get_brand_by_id(test_db, test_brand.id, other_user_id)
        assert exc_info.value.status_code == 403


class TestBrandServiceUpdate:
    """Tests for brand service update function."""

    @pytest.mark.asyncio
    async def test_update_brand_title(self, test_db, test_user, test_brand):
        """Test updating brand title."""
        brand_data = BrandUpdate(title="Updated Title")

        result = await brand_service.update_brand(
            test_db, test_brand.id, test_user.id, brand_data
        )

        assert result.title == "Updated Title"
        assert result.description == test_brand.description

    @pytest.mark.asyncio
    async def test_update_brand_with_images(self, test_db, test_user, test_brand):
        """Test updating brand with new images."""
        brand_data = BrandUpdate(title="Updated Title")
        images = [
            create_mock_upload_file("new1.jpg", b"fake1", "image/jpeg"),
            create_mock_upload_file("new2.jpg", b"fake2", "image/jpeg")
        ]

        with patch("app.services.brand_service.upload_brand_images") as mock_upload, \
             patch("app.services.brand_service.delete_brand_images") as mock_delete:
            mock_upload.return_value = ["s3://bucket/new1.jpg", "s3://bucket/new2.jpg"]

            result = await brand_service.update_brand(
                test_db, test_brand.id, test_user.id, brand_data, images
            )

            assert len(result.product_images) == 2
            mock_delete.assert_called_once()  # Old images deleted


class TestBrandServiceDelete:
    """Tests for brand service delete function."""

    def test_delete_brand_success(self, test_db, test_user, test_brand):
        """Test successful brand deletion."""
        with patch("app.services.brand_service.delete_brand_images") as mock_delete:
            brand_service.delete_brand(test_db, test_brand.id, test_user.id)
            mock_delete.assert_called_once()

            # Verify brand is deleted from database
            deleted_brand = test_db.query(Brand).filter(Brand.id == test_brand.id).first()
            assert deleted_brand is None

    def test_delete_brand_with_active_projects(self, test_db, test_user, test_brand):
        """Test deletion fails with active projects."""
        # Create active project
        project = AdProject(
            id=str(uuid4()),
            user_id=test_user.id,
            brand_id=test_brand.id,
            status="generating"
        )
        test_db.add(project)
        test_db.commit()

        with pytest.raises(HTTPException) as exc_info:
            brand_service.delete_brand(test_db, test_brand.id, test_user.id)
        assert exc_info.value.status_code == 409
