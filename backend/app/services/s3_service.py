"""
S3 service for brand image upload, validation, and deletion.
"""
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import HTTPException, UploadFile, status
from botocore.exceptions import ClientError

from app.config import settings
from app.s3_client import get_s3_client, delete_object
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# Allowed image types
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# File size limits
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
MIN_IMAGES = 2
MAX_IMAGES = 10


def validate_image_file(file: UploadFile) -> None:
    """
    Validate image file type and content type.

    Args:
        file: UploadFile object to validate

    Raises:
        HTTPException: 415 if invalid file type
    """
    # Check content type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Invalid file type: {file.content_type}. Only JPG, PNG, and WEBP are allowed."
        )

    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Invalid file extension: {file_ext}. Only .jpg, .jpeg, .png, and .webp are allowed."
        )


def validate_file_size(file: UploadFile) -> None:
    """
    Validate file size is within limits.

    Args:
        file: UploadFile object to validate

    Raises:
        HTTPException: 413 if file is too large
    """
    # Read file to check size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    if file_size > MAX_FILE_SIZE:
        size_mb = file_size / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size {size_mb:.2f}MB exceeds maximum allowed size of 10MB."
        )


def validate_image_count(count: int) -> None:
    """
    Validate image count is within allowed range.

    Args:
        count: Number of images

    Raises:
        HTTPException: 400 if count is invalid
    """
    if count < MIN_IMAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Minimum {MIN_IMAGES} images required. Provided: {count}"
        )

    if count > MAX_IMAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {MAX_IMAGES} images allowed. Provided: {count}"
        )


async def upload_brand_images(
    user_id: uuid.UUID,
    brand_id: uuid.UUID,
    images: List[UploadFile]
) -> List[str]:
    """
    Upload brand product images to S3.

    Args:
        user_id: User ID owning the brand
        brand_id: Brand ID
        images: List of image files to upload

    Returns:
        List of S3 URLs for uploaded images

    Raises:
        HTTPException: If validation fails or upload fails
    """
    # Validate image count
    validate_image_count(len(images))

    # Validate each image
    for image in images:
        validate_image_file(image)
        validate_file_size(image)

    # Upload images to S3
    s3_urls = []
    s3_client = get_s3_client()

    for image in images:
        try:
            # Generate unique S3 key
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            file_ext = Path(image.filename).suffix.lower()
            unique_id = str(uuid.uuid4())[:8]
            s3_key = f"brands/{user_id}/{brand_id}/{timestamp}_{unique_id}{file_ext}"

            # Read file content
            image.file.seek(0)
            file_content = await image.read()

            # Upload to S3
            s3_client.put_object(
                Bucket=settings.AWS_S3_BUCKET,
                Key=s3_key,
                Body=file_content,
                ContentType=image.content_type
            )

            # Generate S3 URL
            s3_url = f"s3://{settings.AWS_S3_BUCKET}/{s3_key}"
            s3_urls.append(s3_url)

            logger.info(f"Uploaded brand image to S3: {s3_url}")

        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload image to S3: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error during upload: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error during image upload: {str(e)}"
            )

    return s3_urls


def delete_brand_images(image_urls: List[str]) -> None:
    """
    Delete brand images from S3.

    Args:
        image_urls: List of S3 URLs to delete
    """
    for url in image_urls:
        try:
            # Extract S3 key from URL
            # Format: s3://bucket-name/key
            if url.startswith("s3://"):
                parts = url.replace("s3://", "").split("/", 1)
                if len(parts) == 2:
                    s3_key = parts[1]
                    delete_object(s3_key)
                    logger.info(f"Deleted brand image from S3: {s3_key}")
        except Exception as e:
            logger.error(f"Failed to delete S3 object {url}: {e}")
            # Don't raise exception on deletion failure, just log it


def extract_s3_key(s3_url: str) -> Optional[str]:
    """
    Extract S3 key from S3 URL.

    Args:
        s3_url: S3 URL (s3://bucket/key format)

    Returns:
        S3 key or None if invalid URL
    """
    if s3_url.startswith("s3://"):
        parts = s3_url.replace("s3://", "").split("/", 1)
        if len(parts) == 2:
            return parts[1]
    return None
