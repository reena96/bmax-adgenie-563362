"""
S3 Service for handling AWS S3 operations.

This module provides a service class for uploading files to S3, generating presigned URLs,
and managing S3 connections for the Zapcut application.
"""

import logging
import hashlib
import mimetypes
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import uuid4
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from fastapi import UploadFile

from app.config import settings
from app.exceptions import (
    S3UploadError,
    S3ConnectionError,
    InvalidFileError
)

logger = logging.getLogger(__name__)


class S3Service:
    """
    Handles all S3 operations for file uploads and downloads.

    This service manages file uploads to AWS S3 with validation, metadata tagging,
    encryption, and presigned URL generation for secure asset access.
    """

    def __init__(
        self,
        bucket_name: Optional[str] = None,
        region: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None
    ):
        """
        Initialize S3 service with AWS credentials.

        Args:
            bucket_name: S3 bucket name (defaults to settings.s3_bucket_name)
            region: AWS region (defaults to settings.s3_region)
            access_key: AWS access key ID (defaults to settings.aws_access_key_id)
            secret_key: AWS secret access key (defaults to settings.aws_secret_access_key)

        Raises:
            S3ConnectionError: If S3 client cannot be initialized
        """
        self.bucket_name = bucket_name or settings.s3_bucket_name
        self.region = region or settings.s3_region
        self.access_key = access_key or settings.aws_access_key_id
        self.secret_key = secret_key or settings.aws_secret_access_key

        if not self.bucket_name:
            raise S3ConnectionError("S3 bucket name not configured")

        try:
            # Initialize S3 client with credentials
            if self.access_key and self.secret_key:
                self.s3_client = boto3.client(
                    's3',
                    region_name=self.region,
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key
                )
            else:
                # Use default credentials (from IAM role, env vars, etc.)
                self.s3_client = boto3.client('s3', region_name=self.region)

            logger.info(f"S3 service initialized for bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {str(e)}")
            raise S3ConnectionError(f"Failed to initialize S3 client: {str(e)}")

    async def upload_file(
        self,
        file: UploadFile,
        asset_type: str,
        user_id: str,
        project_id: Optional[str] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Upload file to S3 with validation and metadata.

        Args:
            file: The file to upload (FastAPI UploadFile)
            asset_type: Type of asset ('brand_image', 'generated_video', etc.)
            user_id: User ID who is uploading the file
            project_id: Optional project ID for organizing files
            max_retries: Maximum number of retry attempts for transient failures

        Returns:
            Dictionary containing:
                - s3_key: The S3 object key
                - s3_url: Full S3 URL
                - file_size: Size in bytes
                - content_type: MIME type
                - content_hash: MD5 hash of file content

        Raises:
            InvalidFileError: If file validation fails
            S3UploadError: If upload to S3 fails
        """
        if not file.filename:
            raise InvalidFileError("File has no filename")

        try:
            # Read file content
            file_content = await file.read()
            file_size = len(file_content)

            # Reset file position for potential re-reads
            await file.seek(0)

            # Generate unique S3 key
            s3_key = self._generate_s3_key(
                filename=file.filename,
                asset_type=asset_type,
                user_id=user_id,
                project_id=project_id
            )

            # Calculate content hash
            content_hash = hashlib.md5(file_content).hexdigest()

            # Determine content type
            content_type = file.content_type or mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'

            # Set cache control based on asset type
            cache_control = self._get_cache_control(asset_type)

            # Prepare metadata
            metadata = {
                'uploaded_by': user_id,
                'upload_timestamp': datetime.utcnow().isoformat(),
                'content_hash': content_hash,
                'original_filename': file.filename,
                'asset_type': asset_type
            }

            # Upload to S3 with retry logic
            for attempt in range(max_retries):
                try:
                    self.s3_client.put_object(
                        Bucket=self.bucket_name,
                        Key=s3_key,
                        Body=file_content,
                        ContentType=content_type,
                        Metadata=metadata,
                        CacheControl=cache_control,
                        ServerSideEncryption='AES256'  # Enable server-side encryption
                    )

                    logger.info(
                        f"Successfully uploaded file to S3: {s3_key} "
                        f"(size: {file_size} bytes, user: {user_id})"
                    )
                    break
                except (ClientError, BotoCoreError) as e:
                    if attempt < max_retries - 1:
                        # Exponential backoff: 1s, 2s, 4s
                        import asyncio
                        wait_time = 2 ** attempt
                        logger.warning(
                            f"S3 upload attempt {attempt + 1} failed, "
                            f"retrying in {wait_time}s: {str(e)}"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"Failed to upload to S3 after {max_retries} attempts: {str(e)}")
                        raise S3UploadError(f"Failed to upload file to S3: {str(e)}")

            # Construct S3 URL
            s3_url = f"s3://{self.bucket_name}/{s3_key}"

            return {
                's3_key': s3_key,
                's3_url': s3_url,
                'file_size': file_size,
                'content_type': content_type,
                'content_hash': content_hash
            }

        except InvalidFileError:
            raise
        except S3UploadError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during file upload: {str(e)}")
            raise S3UploadError(f"Unexpected error during upload: {str(e)}")

    async def get_presigned_url(
        self,
        s3_key: str,
        expiration_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Generate presigned URL for S3 object access.

        Args:
            s3_key: The S3 object key
            expiration_hours: URL expiration time in hours (max 168 hours / 7 days)

        Returns:
            Dictionary containing:
                - presigned_url: The presigned URL
                - expiration_at: ISO format expiration timestamp

        Raises:
            S3UploadError: If presigned URL generation fails
            ValueError: If expiration_hours exceeds maximum
        """
        # Validate expiration time (max 7 days)
        max_expiration_hours = 168  # 7 days
        if expiration_hours > max_expiration_hours:
            raise ValueError(f"Expiration hours cannot exceed {max_expiration_hours} hours (7 days)")

        expiration_seconds = expiration_hours * 3600
        expiration_at = datetime.utcnow() + timedelta(hours=expiration_hours)

        try:
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration_seconds
            )

            logger.info(f"Generated presigned URL for: {s3_key} (expires: {expiration_at.isoformat()})")

            return {
                'presigned_url': presigned_url,
                'expiration_at': expiration_at.isoformat()
            }

        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to generate presigned URL for {s3_key}: {str(e)}")
            raise S3UploadError(f"Failed to generate presigned URL: {str(e)}")

    async def delete_file(self, s3_key: str) -> bool:
        """
        Delete file from S3.

        Args:
            s3_key: The S3 object key to delete

        Returns:
            True if deletion was successful

        Raises:
            S3UploadError: If deletion fails
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"Deleted S3 object: {s3_key}")
            return True

        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to delete S3 object {s3_key}: {str(e)}")
            raise S3UploadError(f"Failed to delete file: {str(e)}")

    async def check_connection(self) -> bool:
        """
        Test S3 connection for health checks.

        Returns:
            True if S3 connection is healthy, False otherwise
        """
        try:
            # Try to list objects with limit 1 (minimal operation)
            self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                MaxKeys=1
            )
            return True

        except (ClientError, BotoCoreError) as e:
            logger.error(f"S3 health check failed: {str(e)}")
            return False

    def _generate_s3_key(
        self,
        filename: str,
        asset_type: str,
        user_id: str,
        project_id: Optional[str] = None
    ) -> str:
        """
        Generate unique S3 key with proper organization.

        Args:
            filename: Original filename
            asset_type: Type of asset
            user_id: User ID
            project_id: Optional project ID

        Returns:
            S3 key string
        """
        # Sanitize filename (remove special characters, keep only alphanumeric and basic punctuation)
        import re
        sanitized_filename = re.sub(r'[^\w\-_.]', '_', filename)

        # Generate timestamp and UUID for uniqueness
        timestamp = int(datetime.utcnow().timestamp())
        unique_id = str(uuid4())[:8]  # Use first 8 chars of UUID

        # Construct S3 key based on asset type
        if asset_type == 'brand_image':
            s3_key = f"brand-images/{user_id}/{timestamp}_{unique_id}_{sanitized_filename}"
        elif asset_type == 'generated_video':
            if project_id:
                s3_key = f"generated-videos/{project_id}/{timestamp}_{unique_id}_{sanitized_filename}"
            else:
                s3_key = f"generated-videos/{user_id}/{timestamp}_{unique_id}_{sanitized_filename}"
        elif asset_type == 'lora_training':
            s3_key = f"lora-training/{user_id}/{timestamp}_{unique_id}_{sanitized_filename}"
        else:
            # Default organization
            s3_key = f"assets/{user_id}/{asset_type}/{timestamp}_{unique_id}_{sanitized_filename}"

        return s3_key

    def _get_cache_control(self, asset_type: str) -> str:
        """
        Get appropriate cache control header based on asset type.

        Args:
            asset_type: Type of asset

        Returns:
            Cache-Control header value
        """
        if asset_type == 'brand_image':
            # Brand images are immutable, cache for 1 year
            return "public, max-age=31536000, immutable"
        elif asset_type == 'generated_video':
            # Videos may be regenerated, use no-cache
            return "no-cache, must-revalidate"
        else:
            # Default: cache for 1 day
            return "public, max-age=86400"


# Singleton instance for reuse across application
_s3_service_instance: Optional[S3Service] = None


def get_s3_service() -> S3Service:
    """
    Get or create singleton S3 service instance.

    Returns:
        S3Service instance

    Raises:
        S3ConnectionError: If S3 service cannot be initialized
    """
    global _s3_service_instance

    if _s3_service_instance is None:
        _s3_service_instance = S3Service()

    return _s3_service_instance
