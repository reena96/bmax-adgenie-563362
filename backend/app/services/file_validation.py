"""
File validation service for uploaded files.

This module provides comprehensive file validation including MIME type checking,
file size validation, extension validation, and magic byte verification.
"""

import logging
import magic
from typing import Optional, Set
from fastapi import UploadFile

from app.exceptions import FileValidationError

logger = logging.getLogger(__name__)


class FileValidator:
    """
    Validates uploaded files before S3 storage.

    Provides validation for file type (MIME), size, naming, and content integrity
    using magic byte detection.
    """

    # Allowed MIME types
    ALLOWED_IMAGE_TYPES: Set[str] = {'image/jpeg', 'image/png', 'image/webp'}
    ALLOWED_VIDEO_TYPES: Set[str] = {'video/mp4'}

    # Allowed file extensions
    ALLOWED_IMAGE_EXTENSIONS: Set[str] = {'.jpg', '.jpeg', '.png', '.webp'}
    ALLOWED_VIDEO_EXTENSIONS: Set[str] = {'.mp4'}

    # Maximum file sizes
    MAX_IMAGE_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_VIDEO_SIZE: int = 500 * 1024 * 1024  # 500MB
    MAX_FILENAME_LENGTH: int = 255

    # Magic byte signatures for content validation
    MAGIC_BYTES = {
        'image/jpeg': [
            b'\xff\xd8\xff',  # JPEG magic bytes
        ],
        'image/png': [
            b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a',  # PNG magic bytes
        ],
        'image/webp': [
            b'\x52\x49\x46\x46',  # RIFF header (WEBP)
        ],
        'video/mp4': [
            b'\x00\x00\x00',  # MP4 ftyp box (first 3 bytes)
        ]
    }

    @classmethod
    async def validate_image_file(cls, file: UploadFile) -> bool:
        """
        Validate image file (type, size, content).

        Args:
            file: The uploaded file to validate

        Returns:
            True if validation passes

        Raises:
            FileValidationError: If validation fails with specific error message
        """
        if not file.filename:
            raise FileValidationError("File has no filename")

        # Validate filename length
        if len(file.filename) > cls.MAX_FILENAME_LENGTH:
            raise FileValidationError(
                f"Filename '{file.filename}' exceeds maximum length of {cls.MAX_FILENAME_LENGTH} characters"
            )

        # Validate file extension
        extension = cls.get_file_extension(file.filename)
        if extension not in cls.ALLOWED_IMAGE_EXTENSIONS:
            raise FileValidationError(
                f"File '{file.filename}' has invalid extension '{extension}'. "
                f"Allowed extensions: {', '.join(cls.ALLOWED_IMAGE_EXTENSIONS)}"
            )

        # Read file content for validation
        file_content = await file.read()
        await file.seek(0)  # Reset file position

        # Validate file is not empty
        if len(file_content) == 0:
            raise FileValidationError(f"File '{file.filename}' is empty (0 bytes)")

        # Validate file size
        if len(file_content) > cls.MAX_IMAGE_SIZE:
            size_mb = len(file_content) / (1024 * 1024)
            max_mb = cls.MAX_IMAGE_SIZE / (1024 * 1024)
            raise FileValidationError(
                f"File '{file.filename}' is {size_mb:.2f}MB, maximum is {max_mb}MB for images"
            )

        # Validate MIME type using python-magic
        mime_type = cls._detect_mime_type(file_content)
        if mime_type not in cls.ALLOWED_IMAGE_TYPES:
            raise FileValidationError(
                f"File '{file.filename}' has invalid MIME type '{mime_type}'. "
                f"Allowed types: {', '.join(cls.ALLOWED_IMAGE_TYPES)}"
            )

        # Validate magic bytes (file content matches declared type)
        if not cls._validate_magic_bytes(file_content, mime_type):
            raise FileValidationError(
                f"File '{file.filename}' content does not match expected format for {mime_type}"
            )

        logger.info(
            f"Image file validation passed: {file.filename} "
            f"({len(file_content)} bytes, {mime_type})"
        )
        return True

    @classmethod
    async def validate_video_file(cls, file: UploadFile) -> bool:
        """
        Validate video file (type, size, format).

        Args:
            file: The uploaded file to validate

        Returns:
            True if validation passes

        Raises:
            FileValidationError: If validation fails with specific error message
        """
        if not file.filename:
            raise FileValidationError("File has no filename")

        # Validate filename length
        if len(file.filename) > cls.MAX_FILENAME_LENGTH:
            raise FileValidationError(
                f"Filename '{file.filename}' exceeds maximum length of {cls.MAX_FILENAME_LENGTH} characters"
            )

        # Validate file extension
        extension = cls.get_file_extension(file.filename)
        if extension not in cls.ALLOWED_VIDEO_EXTENSIONS:
            raise FileValidationError(
                f"File '{file.filename}' has invalid extension '{extension}'. "
                f"Allowed extensions: {', '.join(cls.ALLOWED_VIDEO_EXTENSIONS)}"
            )

        # Read file content for validation
        file_content = await file.read()
        await file.seek(0)  # Reset file position

        # Validate file is not empty
        if len(file_content) == 0:
            raise FileValidationError(f"File '{file.filename}' is empty (0 bytes)")

        # Validate file size
        if len(file_content) > cls.MAX_VIDEO_SIZE:
            size_mb = len(file_content) / (1024 * 1024)
            max_mb = cls.MAX_VIDEO_SIZE / (1024 * 1024)
            raise FileValidationError(
                f"File '{file.filename}' is {size_mb:.2f}MB, maximum is {max_mb}MB for videos"
            )

        # Validate MIME type
        mime_type = cls._detect_mime_type(file_content)
        if mime_type not in cls.ALLOWED_VIDEO_TYPES:
            raise FileValidationError(
                f"File '{file.filename}' has invalid MIME type '{mime_type}'. "
                f"Allowed types: {', '.join(cls.ALLOWED_VIDEO_TYPES)}"
            )

        # Validate magic bytes
        if not cls._validate_magic_bytes(file_content, mime_type):
            raise FileValidationError(
                f"File '{file.filename}' content does not match expected format for {mime_type}"
            )

        logger.info(
            f"Video file validation passed: {file.filename} "
            f"({len(file_content)} bytes, {mime_type})"
        )
        return True

    @staticmethod
    def get_file_extension(filename: str) -> str:
        """
        Extract and validate file extension.

        Args:
            filename: The filename to extract extension from

        Returns:
            Lowercase file extension including the dot (e.g., '.jpg')
        """
        if '.' not in filename:
            return ''

        extension = '.' + filename.rsplit('.', 1)[1].lower()
        return extension

    @staticmethod
    def _detect_mime_type(file_content: bytes) -> str:
        """
        Detect MIME type from file content using python-magic.

        Args:
            file_content: The file content bytes

        Returns:
            Detected MIME type string
        """
        try:
            mime = magic.Magic(mime=True)
            mime_type = mime.from_buffer(file_content)
            return mime_type
        except Exception as e:
            logger.warning(f"Failed to detect MIME type with magic: {str(e)}")
            return 'application/octet-stream'

    @classmethod
    def _validate_magic_bytes(cls, file_content: bytes, expected_mime: str) -> bool:
        """
        Validate file content magic bytes match expected MIME type.

        Args:
            file_content: The file content bytes
            expected_mime: Expected MIME type

        Returns:
            True if magic bytes match expected type
        """
        if expected_mime not in cls.MAGIC_BYTES:
            # No magic byte validation defined for this type
            return True

        magic_byte_patterns = cls.MAGIC_BYTES[expected_mime]

        for pattern in magic_byte_patterns:
            if file_content.startswith(pattern):
                return True

        # Special case for WEBP - check for WEBP in RIFF header
        if expected_mime == 'image/webp':
            if len(file_content) >= 12:
                # RIFF header + WEBP identifier
                return file_content[0:4] == b'\x52\x49\x46\x46' and file_content[8:12] == b'\x57\x45\x42\x50'

        # Special case for MP4 - check for ftyp box
        if expected_mime == 'video/mp4':
            if len(file_content) >= 8:
                # Check for ftyp box at various positions
                return b'ftyp' in file_content[4:12]

        return False

    @classmethod
    async def validate_file_by_type(cls, file: UploadFile, asset_type: str) -> bool:
        """
        Validate file based on asset type.

        Args:
            file: The uploaded file to validate
            asset_type: Type of asset ('brand_image', 'generated_video', etc.)

        Returns:
            True if validation passes

        Raises:
            FileValidationError: If validation fails
            ValueError: If asset_type is unknown
        """
        if asset_type in ['brand_image', 'b_roll_image']:
            return await cls.validate_image_file(file)
        elif asset_type in ['generated_video', 'scene_video']:
            return await cls.validate_video_file(file)
        else:
            raise ValueError(f"Unknown asset type: {asset_type}")

    @classmethod
    def get_max_file_size(cls, asset_type: str) -> int:
        """
        Get maximum allowed file size for asset type.

        Args:
            asset_type: Type of asset

        Returns:
            Maximum file size in bytes
        """
        if asset_type in ['brand_image', 'b_roll_image']:
            return cls.MAX_IMAGE_SIZE
        elif asset_type in ['generated_video', 'scene_video']:
            return cls.MAX_VIDEO_SIZE
        else:
            return cls.MAX_IMAGE_SIZE  # Default to image size
