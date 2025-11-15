"""
Integration tests for brand management API endpoints.
Tests CRUD operations, image uploads, ownership validation, and error handling.
"""
import io
import json
import pytest
from unittest.mock import patch, MagicMock
from uuid import UUID, uuid4

from fastapi import status

from app.models import User, Brand, AdProject
from app.security import create_access_token, hash_password


@pytest.fixture
def test_user(test_db):
    """Create a test user in the database."""
    user_id = str(uuid4())
    user = User(
        id=user_id,
        email="testuser@example.com",
        name="Test User",
        password_hash="$2b$10$test_hash_for_testing_purposes_only",  # Mock hash
        subscription_tier="free"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def other_user(test_db):
    """Create another test user for ownership validation tests."""
    user_id = str(uuid4())
    user = User(
        id=user_id,
        email="otheruser@example.com",
        name="Other User",
        password_hash="$2b$10$test_hash_for_testing_purposes_only",  # Mock hash
        subscription_tier="free"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Generate auth headers with JWT token."""
    token = create_access_token({"sub": str(test_user.id), "email": test_user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_auth_headers(other_user):
    """Generate auth headers for the other user."""
    token = create_access_token({"sub": str(other_user.id), "email": other_user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_image_file():
    """Create a mock image file for testing."""
    content = b"fake image content"
    return ("image.jpg", io.BytesIO(content), "image/jpeg")


@pytest.fixture
def mock_s3():
    """Mock S3 client for testing."""
    with patch("app.services.s3_service.get_s3_client") as mock:
        s3_client = MagicMock()
        mock.return_value = s3_client
        yield s3_client


@pytest.fixture
def test_brand(test_db, test_user):
    """Create a test brand in the database."""
    brand_id = str(uuid4())
    brand = Brand(
        id=brand_id,
        user_id=test_user.id,
        title="Test Brand",
        description="Test Description",
        product_images=[
            "s3://bucket/brands/user1/brand1/image1.jpg",
            "s3://bucket/brands/user1/brand1/image2.jpg"
        ],
        brand_guidelines={
            "colors": ["#FF0000", "#00FF00"],
            "fonts": ["Arial"],
            "tone": "professional"
        }
    )
    test_db.add(brand)
    test_db.commit()
    test_db.refresh(brand)
    return brand


class TestCreateBrand:
    """Tests for POST /api/brands endpoint."""

    def test_create_brand_success(self, client, auth_headers, mock_s3):
        """Test successful brand creation with images."""
        # Prepare test data
        title = "My Brand"
        description = "Brand description"
        brand_guidelines = json.dumps({
            "colors": ["#FF0000", "#00FF00"],
            "fonts": ["Arial", "Helvetica"],
            "tone": "professional"
        })

        # Mock image files
        image1 = ("image1.jpg", io.BytesIO(b"fake image 1"), "image/jpeg")
        image2 = ("image2.jpg", io.BytesIO(b"fake image 2"), "image/png")

        response = client.post(
            "/api/brands",
            headers=auth_headers,
            data={
                "title": title,
                "description": description,
                "brand_guidelines": brand_guidelines
            },
            files=[
                ("images", image1),
                ("images", image2)
            ]
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == title
        assert data["description"] == description
        assert len(data["product_images"]) == 2
        assert data["brand_guidelines"]["tone"] == "professional"
        assert "id" in data
        assert "created_at" in data

    def test_create_brand_without_auth(self, client):
        """Test brand creation fails without authentication."""
        response = client.post(
            "/api/brands",
            data={"title": "Test Brand"},
            files=[
                ("images", ("image1.jpg", io.BytesIO(b"fake"), "image/jpeg")),
                ("images", ("image2.jpg", io.BytesIO(b"fake"), "image/jpeg"))
            ]
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_brand_less_than_min_images(self, client, auth_headers, mock_s3):
        """Test brand creation fails with less than 2 images."""
        image1 = ("image1.jpg", io.BytesIO(b"fake image 1"), "image/jpeg")

        response = client.post(
            "/api/brands",
            headers=auth_headers,
            data={"title": "Test Brand"},
            files=[("images", image1)]
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Minimum 2 images required" in response.json()["detail"]

    def test_create_brand_more_than_max_images(self, client, auth_headers, mock_s3):
        """Test brand creation fails with more than 10 images."""
        images = [
            ("images", (f"image{i}.jpg", io.BytesIO(b"fake"), "image/jpeg"))
            for i in range(11)
        ]

        response = client.post(
            "/api/brands",
            headers=auth_headers,
            data={"title": "Test Brand"},
            files=images
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Maximum 10 images allowed" in response.json()["detail"]

    def test_create_brand_invalid_file_type(self, client, auth_headers, mock_s3):
        """Test brand creation fails with invalid file type."""
        image1 = ("image1.jpg", io.BytesIO(b"fake"), "image/jpeg")
        image2 = ("document.pdf", io.BytesIO(b"fake pdf"), "application/pdf")

        response = client.post(
            "/api/brands",
            headers=auth_headers,
            data={"title": "Test Brand"},
            files=[("images", image1), ("images", image2)]
        )

        assert response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        assert "Invalid file type" in response.json()["detail"]

    def test_create_brand_file_too_large(self, client, auth_headers, mock_s3):
        """Test brand creation fails with oversized file."""
        # Create a file larger than 10MB
        large_content = b"x" * (11 * 1024 * 1024)
        image1 = ("small.jpg", io.BytesIO(b"fake"), "image/jpeg")
        image2 = ("large.jpg", io.BytesIO(large_content), "image/jpeg")

        response = client.post(
            "/api/brands",
            headers=auth_headers,
            data={"title": "Test Brand"},
            files=[("images", image1), ("images", image2)]
        )

        assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        assert "exceeds maximum allowed size" in response.json()["detail"]

    def test_create_brand_missing_title(self, client, auth_headers, mock_s3):
        """Test brand creation fails without title."""
        image1 = ("image1.jpg", io.BytesIO(b"fake"), "image/jpeg")
        image2 = ("image2.jpg", io.BytesIO(b"fake"), "image/jpeg")

        response = client.post(
            "/api/brands",
            headers=auth_headers,
            data={"description": "Test"},
            files=[("images", image1), ("images", image2)]
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestListBrands:
    """Tests for GET /api/brands endpoint."""

    def test_list_brands_success(self, client, test_db, test_user, auth_headers):
        """Test successful brand listing."""
        # Create multiple brands
        for i in range(3):
            brand = Brand(
                id=str(uuid4()),
                user_id=test_user.id,
                title=f"Brand {i}",
                description=f"Description {i}",
                product_images=[
                    f"s3://bucket/image{i}_1.jpg",
                    f"s3://bucket/image{i}_2.jpg"
                ]
            )
            test_db.add(brand)
        test_db.commit()

        response = client.get("/api/brands", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "brands" in data
        assert "pagination" in data
        assert len(data["brands"]) == 3
        assert data["pagination"]["total"] == 3
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["limit"] == 20

    def test_list_brands_pagination(self, client, test_db, test_user, auth_headers):
        """Test brand listing with pagination."""
        # Create 5 brands
        for i in range(5):
            brand = Brand(
                id=str(uuid4()),
                user_id=test_user.id,
                title=f"Brand {i}",
                product_images=["s3://bucket/image1.jpg", "s3://bucket/image2.jpg"]
            )
            test_db.add(brand)
        test_db.commit()

        # Get page 1 with limit 2
        response = client.get("/api/brands?page=1&limit=2", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["brands"]) == 2
        assert data["pagination"]["total"] == 5
        assert data["pagination"]["has_more"] is True

        # Get page 2
        response = client.get("/api/brands?page=2&limit=2", headers=auth_headers)
        data = response.json()
        assert len(data["brands"]) == 2
        assert data["pagination"]["has_more"] is True

    def test_list_brands_empty(self, client, auth_headers):
        """Test brand listing returns empty list when no brands."""
        response = client.get("/api/brands", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["brands"] == []
        assert data["pagination"]["total"] == 0

    def test_list_brands_without_auth(self, client):
        """Test brand listing fails without authentication."""
        response = client.get("/api/brands")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_brands_ownership_isolation(self, client, test_db, test_user, other_user, auth_headers):
        """Test users only see their own brands."""
        # Create brand for test_user
        brand1 = Brand(
            id=str(uuid4()),
            user_id=test_user.id,
            title="My Brand",
            product_images=["s3://bucket/image1.jpg", "s3://bucket/image2.jpg"]
        )
        # Create brand for other_user
        brand2 = Brand(
            id=str(uuid4()),
            user_id=other_user.id,
            title="Other Brand",
            product_images=["s3://bucket/image1.jpg", "s3://bucket/image2.jpg"]
        )
        test_db.add(brand1)
        test_db.add(brand2)
        test_db.commit()

        response = client.get("/api/brands", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["brands"]) == 1
        assert data["brands"][0]["title"] == "My Brand"


class TestGetBrand:
    """Tests for GET /api/brands/{brand_id} endpoint."""

    def test_get_brand_success(self, client, test_brand, auth_headers):
        """Test successful brand retrieval."""
        response = client.get(f"/api/brands/{test_brand.id}", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_brand.id)
        assert data["title"] == test_brand.title
        assert data["description"] == test_brand.description
        assert len(data["product_images"]) == 2
        assert data["brand_guidelines"]["tone"] == "professional"

    def test_get_brand_not_found(self, client, auth_headers):
        """Test get brand returns 404 for non-existent brand."""
        fake_id = str(uuid4())
        response = client.get(f"/api/brands/{fake_id}", headers=auth_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_brand_ownership_violation(self, client, test_brand, other_auth_headers):
        """Test get brand returns 403 when user doesn't own brand."""
        response = client.get(f"/api/brands/{test_brand.id}", headers=other_auth_headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "permission" in response.json()["detail"].lower()

    def test_get_brand_without_auth(self, client, test_brand):
        """Test get brand fails without authentication."""
        response = client.get(f"/api/brands/{test_brand.id}")

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestUpdateBrand:
    """Tests for PUT /api/brands/{brand_id} endpoint."""

    def test_update_brand_title(self, client, test_brand, auth_headers, mock_s3):
        """Test updating brand title."""
        response = client.put(
            f"/api/brands/{test_brand.id}",
            headers=auth_headers,
            data={"title": "Updated Brand"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Updated Brand"
        assert data["description"] == test_brand.description

    def test_update_brand_with_images(self, client, test_brand, auth_headers, mock_s3):
        """Test updating brand with new images."""
        with patch("app.services.s3_service.delete_brand_images") as mock_delete:
            image1 = ("new1.jpg", io.BytesIO(b"fake"), "image/jpeg")
            image2 = ("new2.jpg", io.BytesIO(b"fake"), "image/jpeg")

            response = client.put(
                f"/api/brands/{test_brand.id}",
                headers=auth_headers,
                data={"title": "Updated Brand"},
                files=[("images", image1), ("images", image2)]
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["product_images"]) == 2
            # Verify old images were deleted
            mock_delete.assert_called_once()

    def test_update_brand_not_found(self, client, auth_headers, mock_s3):
        """Test update brand returns 404 for non-existent brand."""
        fake_id = str(uuid4())
        response = client.put(
            f"/api/brands/{fake_id}",
            headers=auth_headers,
            data={"title": "Updated"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_brand_ownership_violation(self, client, test_brand, other_auth_headers, mock_s3):
        """Test update brand returns 403 when user doesn't own brand."""
        response = client.put(
            f"/api/brands/{test_brand.id}",
            headers=other_auth_headers,
            data={"title": "Hacked"}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_brand_invalid_image_count(self, client, test_brand, auth_headers, mock_s3):
        """Test update fails with invalid image count."""
        image1 = ("new1.jpg", io.BytesIO(b"fake"), "image/jpeg")

        response = client.put(
            f"/api/brands/{test_brand.id}",
            headers=auth_headers,
            files=[("images", image1)]
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestDeleteBrand:
    """Tests for DELETE /api/brands/{brand_id} endpoint."""

    def test_delete_brand_success(self, client, test_brand, auth_headers, mock_s3):
        """Test successful brand deletion."""
        with patch("app.services.s3_service.delete_brand_images") as mock_delete:
            response = client.delete(f"/api/brands/{test_brand.id}", headers=auth_headers)

            assert response.status_code == status.HTTP_204_NO_CONTENT
            # Verify S3 images were deleted
            mock_delete.assert_called_once()

    def test_delete_brand_not_found(self, client, auth_headers):
        """Test delete brand returns 404 for non-existent brand."""
        fake_id = str(uuid4())
        response = client.delete(f"/api/brands/{fake_id}", headers=auth_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_brand_ownership_violation(self, client, test_brand, other_auth_headers):
        """Test delete brand returns 403 when user doesn't own brand."""
        response = client.delete(f"/api/brands/{test_brand.id}", headers=other_auth_headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_brand_with_active_projects(self, client, test_db, test_brand, auth_headers):
        """Test delete brand returns 409 when brand has active projects."""
        # Create an active project for the brand
        project = AdProject(
            id=str(uuid4()),
            user_id=test_brand.user_id,
            brand_id=test_brand.id,
            status="generating"
        )
        test_db.add(project)
        test_db.commit()

        response = client.delete(f"/api/brands/{test_brand.id}", headers=auth_headers)

        assert response.status_code == status.HTTP_409_CONFLICT
        assert "active ad projects" in response.json()["detail"].lower()

    def test_delete_brand_without_auth(self, client, test_brand):
        """Test delete brand fails without authentication."""
        response = client.delete(f"/api/brands/{test_brand.id}")

        assert response.status_code == status.HTTP_403_FORBIDDEN
