"""
Tests for file validation service.

This module tests the FileValidator class for validating image and video files
including MIME type checking, file size validation, and magic byte detection.
"""

import pytest
from io import BytesIO
from fastapi import UploadFile

from app.services.file_validation import FileValidator
from app.exceptions import FileValidationError


class TestFileValidator:
    """Test suite for FileValidator class."""

    # Valid JPEG magic bytes
    VALID_JPEG_BYTES = b'\xff\xd8\xff\xe0' + b'\x00' * 100

    # Valid PNG magic bytes
    VALID_PNG_BYTES = b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a' + b'\x00' * 100

    # Valid WEBP magic bytes (RIFF header + WEBP identifier)
    VALID_WEBP_BYTES = b'\x52\x49\x46\x46' + b'\x00\x00\x00\x00' + b'\x57\x45\x42\x50' + b'\x00' * 100

    # Valid MP4 magic bytes
    VALID_MP4_BYTES = b'\x00\x00\x00\x20\x66\x74\x79\x70' + b'\x00' * 100

    def create_upload_file(self, filename: str, content: bytes, content_type: str) -> UploadFile:
        """Helper to create UploadFile object for testing."""
        file = BytesIO(content)
        return UploadFile(filename=filename, file=file, content_type=content_type)

    @pytest.mark.asyncio
    async def test_validate_valid_jpeg_image(self):
        """Test validation passes for valid JPEG image."""
        file = self.create_upload_file(
            "test.jpg",
            self.VALID_JPEG_BYTES,
            "image/jpeg"
        )
        result = await FileValidator.validate_image_file(file)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_valid_png_image(self):
        """Test validation passes for valid PNG image."""
        file = self.create_upload_file(
            "test.png",
            self.VALID_PNG_BYTES,
            "image/png"
        )
        result = await FileValidator.validate_image_file(file)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_valid_webp_image(self):
        """Test validation passes for valid WEBP image."""
        file = self.create_upload_file(
            "test.webp",
            self.VALID_WEBP_BYTES,
            "image/webp"
        )
        result = await FileValidator.validate_image_file(file)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_valid_mp4_video(self):
        """Test validation passes for valid MP4 video."""
        file = self.create_upload_file(
            "test.mp4",
            self.VALID_MP4_BYTES,
            "video/mp4"
        )
        result = await FileValidator.validate_video_file(file)
        assert result is True

    @pytest.mark.asyncio
    async def test_reject_invalid_image_extension(self):
        """Test validation fails for invalid image extension."""
        file = self.create_upload_file(
            "test.txt",
            self.VALID_JPEG_BYTES,
            "image/jpeg"
        )
        with pytest.raises(FileValidationError) as exc_info:
            await FileValidator.validate_image_file(file)
        assert "invalid extension" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_reject_invalid_video_extension(self):
        """Test validation fails for invalid video extension."""
        file = self.create_upload_file(
            "test.avi",
            self.VALID_MP4_BYTES,
            "video/mp4"
        )
        with pytest.raises(FileValidationError) as exc_info:
            await FileValidator.validate_video_file(file)
        assert "invalid extension" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_reject_empty_file(self):
        """Test validation fails for empty file."""
        file = self.create_upload_file(
            "empty.jpg",
            b'',
            "image/jpeg"
        )
        with pytest.raises(FileValidationError) as exc_info:
            await FileValidator.validate_image_file(file)
        assert "empty" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_reject_oversized_image(self):
        """Test validation fails for oversized image."""
        # Create file larger than 10MB
        large_content = self.VALID_JPEG_BYTES + b'\x00' * (11 * 1024 * 1024)
        file = self.create_upload_file(
            "large.jpg",
            large_content,
            "image/jpeg"
        )
        with pytest.raises(FileValidationError) as exc_info:
            await FileValidator.validate_image_file(file)
        assert "maximum is" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_reject_oversized_video(self):
        """Test validation fails for oversized video."""
        # Create file larger than 500MB (use smaller size for test performance)
        # Just test the logic works
        file = self.create_upload_file(
            "large.mp4",
            self.VALID_MP4_BYTES,
            "video/mp4"
        )
        # Mock the file size check
        large_content = self.VALID_MP4_BYTES + b'\x00' * (501 * 1024 * 1024)
        file.file = BytesIO(large_content)

        with pytest.raises(FileValidationError) as exc_info:
            await FileValidator.validate_video_file(file)
        assert "maximum is" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_reject_filename_too_long(self):
        """Test validation fails for filename exceeding max length."""
        long_filename = "a" * 256 + ".jpg"
        file = self.create_upload_file(
            long_filename,
            self.VALID_JPEG_BYTES,
            "image/jpeg"
        )
        with pytest.raises(FileValidationError) as exc_info:
            await FileValidator.validate_image_file(file)
        assert "exceeds maximum length" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_reject_no_filename(self):
        """Test validation fails when file has no filename."""
        file = self.create_upload_file(
            "",
            self.VALID_JPEG_BYTES,
            "image/jpeg"
        )
        file.filename = None

        with pytest.raises(FileValidationError) as exc_info:
            await FileValidator.validate_image_file(file)
        assert "no filename" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_validate_file_by_type_brand_image(self):
        """Test validate_file_by_type works for brand_image."""
        file = self.create_upload_file(
            "brand.jpg",
            self.VALID_JPEG_BYTES,
            "image/jpeg"
        )
        result = await FileValidator.validate_file_by_type(file, "brand_image")
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_file_by_type_generated_video(self):
        """Test validate_file_by_type works for generated_video."""
        file = self.create_upload_file(
            "video.mp4",
            self.VALID_MP4_BYTES,
            "video/mp4"
        )
        result = await FileValidator.validate_file_by_type(file, "generated_video")
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_file_by_type_invalid_type(self):
        """Test validate_file_by_type raises error for unknown asset type."""
        file = self.create_upload_file(
            "test.jpg",
            self.VALID_JPEG_BYTES,
            "image/jpeg"
        )
        with pytest.raises(ValueError) as exc_info:
            await FileValidator.validate_file_by_type(file, "unknown_type")
        assert "unknown asset type" in str(exc_info.value).lower()

    def test_get_file_extension(self):
        """Test file extension extraction."""
        assert FileValidator.get_file_extension("test.jpg") == ".jpg"
        assert FileValidator.get_file_extension("test.JPEG") == ".jpeg"
        assert FileValidator.get_file_extension("test.png") == ".png"
        assert FileValidator.get_file_extension("no_extension") == ""
        assert FileValidator.get_file_extension("multiple.dots.jpg") == ".jpg"

    def test_get_max_file_size(self):
        """Test getting maximum file size for asset types."""
        assert FileValidator.get_max_file_size("brand_image") == 10 * 1024 * 1024
        assert FileValidator.get_max_file_size("generated_video") == 500 * 1024 * 1024
        assert FileValidator.get_max_file_size("b_roll_image") == 10 * 1024 * 1024
        assert FileValidator.get_max_file_size("scene_video") == 500 * 1024 * 1024
